import urlparse
import urllib
import logging
import json
import dateutil.parser
import difflib

import tornado.web
import tornado
from tornado import gen
from tornado.httpclient import AsyncHTTPClient

from base.handlers import BaseHandler
from smlr.apps.api.mixins import BaseApiMixin as SmlrBaseApiMixin


logger = logging.getLogger('recommend_me')


def title_diff(t1, t2):
    return difflib.SequenceMatcher(None, t1, t2).real_quick_ratio()


def get_youtube_embeded_link(link):
    if not link:
        return None
    parsed = urlparse.urlparse(link)
    if link:
        if 'youtube.com' in parsed.hostname \
        and 'youtube.com/embed' not in link:
            parsed_qs = urlparse.parse_qs(parsed.query)
            try:
                video_id = parsed_qs['v'][0]
            except (KeyError, IndexError):
                return None
            link = 'http://www.youtube.com/embed/%s' % video_id
        elif 'youtu.be' in parsed.hostname:
            video_id = parsed.path[1:]
            if not video_id:
                return None
            link = 'http://www.youtube.com/embed/%s' % video_id
        return link


class ItemInfoHander(SmlrBaseApiMixin, BaseHandler):

    @tornado.web.asynchronous
    @gen.engine
    def get(self, category, item_id):
        result = yield gen.Task(
            self.async_db.items.find_one,
            {'id': item_id}
        )
        if not result.args[0]:
            raise tornado.web.HTTPError(404)
        item = result.args[0]
        item.setdefault('details', {}).setdefault('attributes', {})
        for k, v in item['details']['attributes'].items():
            if type(v) != list:
                item['details']['attributes'][k] = [v]
        user_id = yield gen.Task(self.get_current_user_id_async)
        current_user_mark = yield gen.Task(
            self.item_account_mark,
            item_id, user_id, item['category']
        )

        is_liked = False
        is_disliked = False
        is_bookmarked = False
        if current_user_mark:
            if current_user_mark == 1:
                is_liked = True
            if current_user_mark == -1:
                is_disliked = True
            if current_user_mark == 0.1:
                is_bookmarked = True
        binding = {
            'movies': 'movie',
            'music': 'artist',
            'books': 'book',
            'television': 'tv_show',
            'games': 'game'
        }
        self.jinja_render(
            'collection/item.html', item=item, category=category,
            is_liked=is_liked, is_disliked=is_disliked,
            is_bookmarked=is_bookmarked,
            youtube_embeded_link=get_youtube_embeded_link(
                item.get('details', {}).get('video')
            ),
            og_type=binding.get(item['category'], 'movie')
        )


class UpdateItemInfoHandler(tornado.auth.FacebookGraphMixin, BaseHandler):

    @gen.engine
    def get_facebook_info(self, item, category, callback):

        def spliter(str, lower=False):
            results = [
                a.strip() for a in str \
                    .replace(' and ', ', ').replace('\n', ', ').split(', ')
            ]
            if lower:
                results = [r.lower() for r in results]
            return results

        details = {}
        data = yield gen.Task(
            self.facebook_request,
            '/%s' % item['id']
        )
        if not data:
            callback(data)
            return
        details['likes'] = data['likes']
        details['category'] = data.get('category')
        if data.get('website'):
            details['website'] = data.get('website')
        if data.get('description'):
            details['description'] = data.get('description')
        details['attributes'] = {}
        if data.get('release_date'):
            try:
                release_date = dateutil.parser.parse(data['release_date'])
                details['attributes']['year'] = release_date.year
            except ValueError:
                pass
        if data.get('isbn'):
            details['attributes']['isbn'] = data['isbn']
        if data.get('author'):
            details['attributes']['authors'] = spliter(data['author'])
        if data.get('written_by'):
            details['attributes']['writing'] = spliter(data['written_by'])
        if data.get('starring'):
            details['attributes']['actors'] = spliter(data['starring'])
        if data.get('directed_by'):
            details['attributes']['directing'] = spliter(data['directed_by'])
        if data.get('hometown'):
            details['attributes']['hometown'] = data['hometown']
        if data.get('band_members'):
            details['attributes']['members'] = spliter(data['band_members'])
        if data.get('influences'):
            details['attributes']['influences'] = spliter(data['influences'])
        if data.get('current_location'):
            details['attributes']['current location'] = data['current_location']
        if data.get('network'):
            details['attributes']['network'] = spliter(data['network'])
        if data.get('schedule'):
            details['attributes']['schedule'] = data['schedule']
        if data.get('genre'):
            details['tags'] = spliter(data['genre'], True)
        if data.get('name'):
            details['name'] = data['name']
        if data.get('link'):
            details['link'] = data['link']
        callback(details)

    @gen.engine
    def get_lastfm_info(self, item_name, details, callback):
        response = yield gen.Task(
            self.http_client.fetch,
            "http://ws.audioscrobbler.com/2.0/?%s" % urllib.urlencode({
                'method': 'artist.getinfo',
                'artist': item_name.encode('utf-8'),
                'api_key': self.settings['lastfm_api_key'],
                'format': 'json'
            })
        )
        artist_info = json.loads(response.body)
        if 'error' not in artist_info:
            description = artist_info['artist'].get('bio', {}).get('summary')
            if description:
                details['description'] = description
            try:
                details['image'] = [
                    im['#text'] for im in artist_info['artist']['image']\
                        if im['size'] == 'large'
                ][0]
            except (IndexError, KeyError):
                pass
            try:
                details['image_large'] = [
                    im['#text'] for im in artist_info['artist']['image'] \
                        if im['size'] == 'extralarge'
                ][0]
            except (IndexError, KeyError):
                pass
            try:
                details['tags'] = [
                    tag['name'] for tag in artist_info['artist']['tags']['tag']
                ]
            except (IndexError, KeyError, TypeError):
                pass
        callback(details)

    @gen.engine
    def get_tmdb_info(self, item_name, details, callback):
        year = details.get('attributes', {}).get('year')
        # Trying to search without year
        query = item_name.encode('utf-8')
        response = yield gen.Task(
            self.http_client.fetch,
            "http://api.themoviedb.org/2.1/Movie.search/en/json/%s/%s" % (
                self.settings['tmdb_api_key'], urllib.quote_plus(query)
            )
        )
        try:
            results = json.loads(response.body)
        except (IndexError, ValueError):
            logger.debug('No tmdb data found for movie "%s"' % item_name)
            callback(details)
            return
        else:
            if results == [u'Nothing found.']:
                callback(details)
                return
            results = sorted(results, key=lambda r: -r.get('popularity', 0))
            data = results.pop()
            diff = title_diff(data['name'], query)
            for result in results:
                try:
                    new_diff = title_diff(result['name'], query)
                    if new_diff > diff:
                        data = result
                        diff = new_diff
                    elif new_diff == diff:
                        if year and data.get('released', '')[:4] != str(year) \
                        and result.get('released', '')[:4] == str(year):
                            data = result
                        elif result.get('released', '')[:4] == data.get('released', '')[:4] \
                        and data.get('language', '') != 'en' \
                        and result.get('language', '') == 'en':
                            data = result
                except TypeError:
                    pass
        try:
            tmdb_id = data['id']
        except TypeError:
            callback(details)
            return
        response = yield gen.Task(
            self.http_client.fetch,
            "http://api.themoviedb.org/2.1/Movie.getInfo/en/json/%s/%s" % (
                self.settings['tmdb_api_key'], tmdb_id
            )
        )
        try:
            data = json.loads(response.body)[0]
        except IndexError:
            logger.debug('No tmdb data found for movie "%s"' % item_name)
            callback(details)
            return
        except ValueError:
            logger.debug('Error parsing json for movie "%s"' % item_name)
            callback(details)
            return
        #logger.debug('TMDB data for movie "%s": %s' % (item_name, data))
        if data.get('overview'):
            details['description'] = data['overview']
        if data.get('trailer'):
            details['video'] = data.get('trailer')
        try:
            details['image'] = [
                p['image']['url'] for p in data['posters'] \
                    if p['image']['size'] == 'thumb'
            ][0]
        except IndexError:
            pass
        try:
            details['image_large'] = [
                p['image']['url'] for p in data['posters'] \
                    if p['image']['size'] == 'w342'
            ][0]
        except IndexError:
            try:
                details['image_large'] = [
                p['image']['url'] for p in data['posters'] \
                    if p['image']['size'] == 'cover'
            ][0]
            except IndexError:
                pass
        details['tags'] = [g['name'].lower() for g in data['genres']]
        details.setdefault('attributes', {})
        if data.get('released') and 'year' not in details['attributes']:
            details['attributes']['year'] = data['released'].split('-', 1)[0]
        if data.get('studios') and 'studios' not in details['attributes']:
            details['attributes']['studios'] = [s['name'] for s in data.get('studios')]
        if data.get('countries') and 'countreis' not in details['attributes']:
            details['attributes']['countries'] = [s['name'] for s in data.get('countries')]
        original_attributes = details['attributes'].keys()
        for cast_item in data.get('cast'):
            department = cast_item['department'].lower()
            if department in original_attributes:
                del original_attributes[original_attributes.index(department)]
                del details['attributes'][department]
            details['attributes'].setdefault(
                department, []
            ).append(cast_item['name'])
        if data.get('runtime') and 'runtime' not in details['attributes']:
            details['attributes']['runtime'] = data['runtime']
        if data.get('budget') and 'budget' not in details['attributes']:
            details['attributes']['budget'] = data['budget']
        if data.get('revenue') and 'revenue'not in details['attributes']:
            details['attributes']['revenue'] = data['revenue']
        callback(details)

    def get_amazon_info(self, item_name, category, details):
        AMAZON_LINK_TEMPLATE = 'http://www.amazon.com/gp/search?ie=UTF8&' \
            'keywords=%s&tag=reccome-20&index=%s&' \
            'linkCode=ur2&camp=1789&creative=9325'
        subitems = details.get('subitems')
        if not subitems:
            details['subitems'] = [{'title': item_name}]
            subitems = details.get('subitems')
        for index, item in enumerate(subitems):
            details['subitems'][index].setdefault('amazon_links', {})
            details['subitems'][index]['amazon_links']
            if category == 'movies':
                details['subitems'][index]['amazon_links']['Instant Video'] = \
                    AMAZON_LINK_TEMPLATE % (item['title'], 'amazontv')
                details['subitems'][index]['amazon_links']['DVD'] = \
                    AMAZON_LINK_TEMPLATE % (item['title'], 'dvd')
            elif category == 'music':
                details['subitems'][index]['amazon_links']['Music'] = \
                    AMAZON_LINK_TEMPLATE % (item['title'], 'music')
                details['subitems'][index]['amazon_links']['Digital Music'] = \
                    AMAZON_LINK_TEMPLATE % (item['title'], 'digital-music')
            elif category == 'books':
                details['subitems'][index]['amazon_links']['Books'] = \
                    AMAZON_LINK_TEMPLATE % (item['title'], 'music')
                details['subitems'][index]['amazon_links']['Kindle Store'] = \
                    AMAZON_LINK_TEMPLATE % (item['title'], 'digital-text')
            elif category == 'television':
                details['subitems'][index]['amazon_links']['DVD'] = \
                    AMAZON_LINK_TEMPLATE % (item['title'], 'dvd')
                details['subitems'][index]['amazon_links']['Instant Video'] = \
                    AMAZON_LINK_TEMPLATE % (item['title'], 'amazontv')
            elif category == 'games':
                details['subitems'][index]['amazon_links']['Toys and Games'] = \
                    AMAZON_LINK_TEMPLATE % (item['title'], 'toys-and-games')
                details['subitems'][index]['amazon_links']['Video Game'] = \
                    AMAZON_LINK_TEMPLATE % (item['title'], 'videogames')
        return details

    @gen.engine
    def get_itunes_info(self, item_name, category, details, callback):
        query = {
            'term': item_name.encode('utf-8', 'ignore')
        }
        limit = 1
        exact_name = False
        if category == 'movies':
            query.update({
                'media': 'movie',
                'entity': 'movie',
                'attribute': 'movieTerm'
            })
        elif category == 'music':
            query.update({
                'media': 'music',
                'entity': 'musicArtist',
                'attribute': 'artistTerm'
            })
        elif category == 'books':
            query.update({
                'media': 'ebook',
                'entity': 'ebook'
            })
            limit = 10
        elif category == 'television':
            query.update({
                'media': 'tvShow',
                'entity': 'tvSeason',
                'attribute': 'tvSeasonTerm'
            })
            limit = False
            exact_name = True
        elif category == 'games':
            query.update({
                'media': 'software'
            })
        response = yield gen.Task(
            self.http_client.fetch,
            "http://itunes.apple.com/search?%s" % urllib.urlencode(query)
        )
        if not response:
            logger.info("Can't find itunes info for query %s" % query)
            callback(details)
        response = json.loads(response.body)
        details['subitems'] = []
        results = response.get('results', [])
        if limit:
            results = results[:limit]
        for item in results:
            title = item.get(
                'artistName',
                item.get(
                    'collectionName',
                    item.get('trackName')
                )
            )
            if exact_name and title.lower() != item_name.lower():
                # TODO: allow small differents
                continue
            details['subitems'].append({
                'title': item.get(
                    'collectionName',
                    item.get(
                        'trackName',
                        item.get('artistName')
                    )
                ),
                'url': item.get(
                    'collectionViewUrl',
                    item.get(
                        'trackViewUrl',
                        item.get('artistLinkUrl')
                    )
                ),
                'image': item.get('artworkUrl100'),
                'image_small': item.get('artworkUrl60'),
            })
            if not details.get('itunes_link'):
                details['itunes_link'] = item.get(
                    'artistViewUrl', item.get(
                        'artistLinkUrl',
                        item.get('trackViewUrl')
                    )
                )
            if 'primaryGenreName' in item \
            and item['primaryGenreName'].lower() not in details.get('tags', []):
                details.setdefault('tags', []).append(item['primaryGenreName'].lower())
            if 'longDescription' in item:
                details['description'] = item['longDescription']
            if 'artworkUrl100' in item and 'image' not in details:
                details['image'] = item.get('artworkUrl100')
                if details['image'] and '100x100' in details['image']:
                    # Some hacking here
                    details['image_large'] = details['image'].replace(
                        '100x100', '200x200'
                    )
            if 'artworkUrl60' in details and 'image_small' not in details:
                details['image_small'] = item.get('artworkUrl60')
            details.setdefault('attributes', {})
            if 'year' not in details['attributes'] and 'releaseDate' in item:
                details['attributes']['year'] = item['releaseDate'][:4]
            if 'country' not in details['attributes'] and 'countries' in item:
                details['attributes']['countries'] = [item['country']]
        callback(details)

    @tornado.web.asynchronous
    @gen.engine
    def get(self, item_id):
        logger.debug('Fetching details for item %s' % item_id)
        result = yield gen.Task(
            self.async_db.items.find_one,
            {'id': item_id},
            fields=['id', 'details', 'category', 'name']
        )
        item = result.args[0]
        if not item:
            raise tornado.web.HTTPError(404)
        self.http_client = AsyncHTTPClient()
        if 'details' not in item or item['details'].get('parsed_version') != \
        self.settings['parsed_version']:
            # cleaning name
            item_name = item['name'].split('(')[0]
            item_name = item_name.replace('Official', '').replace('"', '').strip()
            details = yield gen.Task(
                self.get_facebook_info,
                item, item['category']
            )
            # TODO: Limit facebook details
            if not details:
                details = {}
            details['parsed_version'] = self.settings['parsed_version']
            details = yield gen.Task(
                self.get_itunes_info,
                item_name, item['category'],
                details
            )
            amazon_data = self.get_amazon_info(
                item_name, item['category'], details
            )
            details.update(amazon_data)

            if item['category'] == 'music':
                details = yield gen.Task(
                    self.get_lastfm_info, item_name, details
                )
            elif item['category'] == 'movies':
                details = yield gen.Task(
                    self.get_tmdb_info, item_name, details
                )
            yield gen.Task(
                self.async_db.items.update,
                {'id': item['id']}, {'$set': {'details': details, 'name': item_name}}
            )
            result = yield gen.Task(
                self.async_db.items.find_one, {'id': item['id']},
                fields=['id', 'details']
            )
            item = result.args[0]
        if '_id' in item:
            del item['_id']
        self.add_header('Content-Type', 'application/json')
        self.finish(json.dumps(item))
