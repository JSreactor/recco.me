var recco = (function() {
    return {
        currentItemsCount: 0,
        totalItemsCount: null,
        init: function() {
            
        },
        infinityScrollerProcessing: false,
        infinityScroller: function(callback, bottomPixels) {
            if (bottomPixels === undefined)
                bottomPixels = 50;
            $(document).scroll(function() {
                var isScrollable = $(document).height() - $(window).height() <= $(window).scrollTop() + bottomPixels;
                if (isScrollable && !recco.infinityScrollerProcessing) {
                    recco.infinityScrollerProcessing = true;
                    callback(function () {
                        recco.infinityScrollerProcessing = false;
                    });
                }
            });
        },
        reloadRecommendations: function(category, tag, fromCache, callback) {
            var resultList = $('#results .resultList');
            recco.loadRecommendations(category, tag, resultList, false, Math.max(15, recco.currentItemsCount), 0, fromCache, function(response) {
                if (response.items !== undefined) {
                    recco.currentItemsCount = response.items.length;
                }
                else {
                    $('.no-results-message').show();
                }
                if (callback !== undefined)
                    callback();
            });
        },
        moreRecommendations: function(category, tag, callback) {
            var resultList = $('#results .resultList');
            if (recco.totalItemsCount && recco.currentItemsCount >= recco.totalItemsCount) {
                if (callback)
                    callback();
                return;
            }
            recco.loadRecommendations(category, tag, resultList, true, 15, recco.currentItemsCount, true, function(response) {
                    if (response.items !== undefined) {
                        recco.currentItemsCount += response.items.length;
                    }
                    if (callback !== undefined)
                        callback();
                }
            );
        },
        loadRecommendations: function(
            category, tag, resultList, isAppend, limit, skip, fromCache, callback
        ) {
            $.getJSON(
                '/' + category + '/?limit=' + limit + '&skip=' + skip +
                '&tag=' + tag + '&friends_only=' + FRIENDS_ONLY +
                '&get_from_cache=' + fromCache,
                function(response
            ) {
                // height hack
                $('#results').css('height', $('#results').height() + "px");

                if (isAppend !== undefined && isAppend) {
                    resultList.show();
                } else {
                    resultList.empty();
                    resultList.show();
                }
                $('#update-progress-bar').hide();
                $('#update-progress-status').hide();

                if (response.status == 'ok' || response.status == 'no-recommendations') {
                    var html = '';
                    if (response.status == 'no-recommendations') {
                        $('#recommended-items-count').parent().hide();
                        $('#no-results-message').show();
                    } else {
                        $('#recommended-items-count').text(response.items_count);
                        $('#recommended-items-count').parent().show();
                        $('#no-results-message').hide();
                    }
                    recco.totalItemsCount = response.items_count;
                    for (var i in response.items) {
                        item = response.items[i];
                        var imageUrl = null;
                        var itemUrl = null;
                        if (item.info.details === undefined || item.info.details.image_large === undefined)
                            imageUrl = 'http://graph.facebook.com/'+ item.info.id + '/picture?type=large';
                        else if (item.info.details.image_large !== undefined)
                            imageUrl = item.info.details.image_large;
                        itemUrl = '/' + category + '/' + item.info.id + '/';
                        var tags = '';
                        // if (item.info.details != undefined && item.info.details.tags != undefined) {
                        //     for (var t in item.info.details.tags) {
                        //         tag = item.info.details.tags[t];
                        //         tags += '<li class="b-tags__item b-iblock">'
                        //           + '<a class="b-tags__link b-iblock" href="#">'
                        //             +'<span>' + tag + '</span>'
                        //           + '</a>'
                        //         + '</li> ';
                        //     }
                        // }
                        if (response.status == 'no-recommendations')
                            item.relevance = '';
                        var link = '';
                        if (item.info !== undefined && item.info.details !== undefined)
                            link = item.info.details.link;
                        html += '<li id="list-item-' + item.info.id + '" data-id="' + item.info.id + '" data-relevance="' + item.relevance + '">' +
                            '<div class="imgCont">' +
                              '<a class="b-imgCont__link item-info" href="' + itemUrl + '">' +
                                '<img class="item-image" src="' + imageUrl + '" alt="' + item.info.name +'"/>' +
                              '</a>' +
                            '</div>' +
                            '<div class="infoCont b-iblock">' +
                              '<h3 class="b-iblock"><a class="item-info" href="' + itemUrl + '">' +
                                item.info.name +
                              '</a></h3>' +
                              '<form action="/hide/" method="post" accept-charset="utf-8">' +
                                '<input type="hidden" name="item_id" value="' + item.info.id + '">' +
                                '<input type="hidden" name="category" value="' + category + '">' +
                                '<input type="hidden" name="item_' + item.info.id + '_name" value="' + item.info.name + '">' +
                                '<button class="invite ignore" type="submit" >×</button>' +
                              '</form>' +
                              '<div class="like-dislike-hide">' +
                                // item.relevance +
                                '<form class="b-form-like" action="/like/" method="post" accept-charset="utf-8">' +
                                  '<input type="hidden" name="item_id" value="' + item.info.id + '">' +
                                  '<input type="hidden" name="category" value="' + category + '">' +
                                  '<input type="hidden" name="item_' + item.info.id + '_name" value="' + item.info.name + '">' +
                                  '<input type="hidden" name="item_url" value="' + link + '">' +
                                  '<button class="b-button b-button-like b-iblock" type="submit">' +
                                    '<i class="b-button-icon b-button-icon__like"></i>' +
                                    '<span>like</span>' +
                                  '</button>' +
                                '</form>' +
                                '<form class="b-form-like" action="/dislike/" method="post" accept-charset="utf-8">' +
                                  '<input type="hidden" name="item_id" value="' + item.info.id + '">' +
                                  '<input type="hidden" name="category" value="' + category + '">' +
                                  '<input type="hidden" name="item_' + item.info.id + '_name" value="' + item.info.name + '">' +
                                  '<button class="b-button b-button-like b-iblock" type="submit">' +
                                    '<i class="b-button-icon b-button-icon__dislike"></i>' +
                                    '<span>Dislike</span>' +
                                  '</button>' +
                                '</form>' +
                                '<form class="b-form-like" action="/bookmark/" method="post" accept-charset="utf-8">' +
                                  '<input type="hidden" name="item_id" value="' + item.info.id + '">' +
                                  '<input type="hidden" name="category" value="' + category + '">' +
                                  '<input type="hidden" name="item_' + item.info.id + '_name" value="' + item.info.name + '">' +
                                  '<button class="b-button favor" type="submit"></button>' +
                                '</form>' +
                              '</div>' +
                              // + '<ul class="b-tags__list">'
                              //   + tags
                              // + '</ul>'
                            '</div>' +
                        '</li>';
                    }
                    if (isAppend)
                        resultList.append(html);
                    else
                        resultList.html(html);
                    for (i in response.items) {
                        item = response.items[i];
                        if (item.info.details === undefined ||
                            item.info.details.parsed_version === undefined ||
                            item.info.details.parsed_version != PARSED_VERSION
                        )
                            recco.updateItemInfo(item.info.id);
                    }
                    recco.loadFriendsActivityFeed(CURRENT_USER_ID, 0, category);
                    // height hack
                    $('#results').css('height', 'auto');
                    if (callback !== undefined)
                        callback(response);
                }
            });
        },
        // loadItemInfo: function(id, callback) {
        //     $.getJSON('/item-info/' + id + '/', function(item) {
        //         var subitems_html = '';
        //         if (item.details.subitems !== undefined) {
        //             subitems_html = '<div class="b-buy__block">' +
        //                 '<li class="b-buy__item b-itunes b-iblock">&nbsp;</li>' +
        //                 '<li class="b-buy__item b-itunes b-iblock"><a href="#">iTunes</a></li>' +
        //                 '<li class="b-buy__item b-amazon b-iblock"><a href="#">Amazon</a></li>' +
        //                 '<li class="b-buy__item b-custom b-iblock"><a href="#">Custom</a></li>' +
        //             '</div>';
        //             for (var i in item.details.subitems) {
        //                 var link = item.details.subitems[i];
        //                 var image_html = '';
        //                 if (link.image_small) {
        //                     image_html = '<img src="' + link.image_small + '"/> ';
        //                 } else {
        //                     var imageUrl = null;
        //                     if (item.details === undefined || item.details.image === undefined)
        //                         imageUrl = 'http://graph.facebook.com/'+ item.id + '/picture?type=normal';
        //                     else
        //                         imageUrl = item.details.image;
        //                     image_html = '<img src="' + imageUrl + '"/> ';
        //                 }
        //                 amazon_links_html = '';
        //                 for (var title in link.amazon_links)
        //                     amazon_links_html += '<li class="b-buy__item b-itunes b-iblock">' +
        //                         '<a class="b-buy__link" href="' + link.amazon_links[title] + '">' +
        //                           title +
        //                         '</a>' +
        //                     '</li>';
        //                 bitems_html += '<div class="b-buy__block">' +
        //                     '<li class="b-buy__item b-iblock">' +
        //                       '<a class="b-buy__img b-iblock" href="#">' +
        //                         image_html +
        //                       '</a> '  +
        //                     '<span class="b-buy__text b-iblock">' + link.title + '</span>' +
        //                     '</li>' +
        //                     '<li class="b-buy__item b-itunes b-iblock">' +
        //                       '<a class="b-buy__link" href="'+ link.link + '">' +
        //                         link.title +
        //                       '</a>' +
        //                     '</li>' +
        //                     amazon_links_html +
        //                 '</div>';
        //             }
        //         }
        //         var attributes_html = '';
        //         if (item.details.attributes !== undefined)
        //             for (var attr_name in item.details.attributes) {
        //                 var attr_value = item.details.attributes[attr_name];
        //                 var attr_values_html = '';
        //                 if (typeof(attr_value) == 'object') {
        //                     for (var v in attr_value)
        //                         attr_values_html += '<span>' + attr_value[v] + '</span>, ';
        //                     attr_values_html = attr_values_html.slice(0, -2);
        //                 }
        //                 else
        //                     attr_values_html = attr_value;
        //                 attributes_html += '<li class="b-description__item">' +
        //                     '<span class="b-name-category b-iblock">' + attr_name + '</span>' +
        //                     '<span class="b-category b-iblock">' + attr_values_html + '</span>' +
        //                 '</li>';
        //             }
        //         var html = '<div class="item-details b-description" style="display:none">' +
        //             '<a class="b-description__close b-description__close_top" href="#"></a>' +
        //             '<a class="b-description__close b-description__close_bottom" href=""></a>' +
        //             '<div class="fb-facepile" data-href="' + item.details.link + '" data-width="400" data-max-rows="2"></div>' +
        //             '<p>' + item.details.description + '</p>' +
        //             '<ul class="b-description__list">' + attributes_html + '</ul>' +
        //             '<div class="b-buy">' +
        //               '<h4>Where to get</h4>' +
        //                 '<ul class="b-buy__list">' + subitems_html + '</ul>' +
        //             '</div>' +
        //         '</div>';
        //         $('#list-item-' + item.id).find('.like-dislike-hide').after(html);
        //         FB.XFBML.parse();
        //         if (callback)
        //             callback();
        //     });
        // },
        updateItemInfo: function(id) {
            $.getJSON('/update-item-info/' + id + '/', function(response) {
                $('#list-item-' + id).find('a.link-with-name')
                    .text(response.details.name);
                var image_src = 'http://graph.facebook.com/'+ id + '/picture?type=large';
                if (response.details.image_large !== undefined)
                    image_src = response.details.image_large;
                if ('image' in response.details)
                    $('#list-item-' + id).find('.item-image').attr(
                        'src', image_src
                    );
                if (CURRENT_TAG !== undefined && CURRENT_TAG && (!(CURRENT_TAG in response.details.tags) || response.details.tags))
                    $('#list-item-' + id).remove();
                // if ('tags' in response.details)
                //     $('#list-item-' + id).find('.b-tags__list').html(
                //         function() {
                //             var tags = '';
                //             for (var i in response.details.tags) {
                //                 var tag = response.details.tags[i];
                //                 tags += '<li class="b-tags__item b-iblock">'
                //                   + '<a class="b-tags__link b-iblock" href="#">'
                //                     +'<span>' + tag + '</span>'
                //                   + '</a>'
                //                 + '</li> ';
                //             }
                //             return tags
                //         }()
                //     );
            });
        },
        updateProfileFull: function(category, tag) {
            if (tag === undefined)
                tag = '';
            var conn = new io.connect(
                'http://' + window.location.hostname + ':' + SOCKET_IO_PORT + '/update-profile/',
                {'reconnect': false}
            );
            var friends_total_count = null;
            var friends_parsed_count = 0;
            conn.on('connect', function() {
                conn.emit('do_update', category);
                $('#results .resultList').hide();
                $('#update-progress-bar').show();
                $('#update-progress-bar span').css('width', '1%');
                $('#update-progress-bar span').animate({width: '10%'});
                $('#update-progress-bar span').text("5%");
                $('#update-progress-status').text( 'Processing your interests...');
                $('#update-progress-status').show();
            });
            conn.on('update-profile-friends-count', function(count) {
                friends_total_count = count;
                $('#update-progress-bar span').animate({width: '20%'});
                $('#update-progress-bar span').text("20%");
                $('#update-progress-status').text('Processing your friends interests...');
            });
            conn.on('update-profile-new-data', function(data) {
                friends_parsed_count += 1;
                percent = friends_parsed_count / friends_total_count * 80 + 20;
                percent = percent.toFixed();
                $('#update-progress-bar span').css('width', percent + "%");
                $('#update-progress-bar span').text(percent + "%");
            });
            conn.on('update-profile-finish', function(data) {
                conn.disconnect();
                conn = null;
                $('#update-progress-status').text(
                    'Finish processing. Generating recommendations...'
                );
                recco.reloadRecommendations(category, tag, false);
            });
        },
        addAutocomplete: function(el, category) {
            var categories = [];
            if (category == 'movies')
                categories = ['movie'];
            else if (category == 'books')
                categories = ['book', 'author'];
            else if (category == 'television')
                categories = ['tv show'];
            else if (category == ['games'])
                categories = ['games/toys'];
            else if (category == 'music')
                categories = ['musician/band', 'artist'];
            $(el).autocomplete({
                source: function(request, callback) {
                    FB.api('/search?q=' + request.term + '&type=page', function(response) {
                        var results = [];
                        for (var i in response.data) {
                            var item = response.data[i];
                            if (categories.indexOf(item.category.toLowerCase()) >= 0) {
                                results.push({
                                    'image': 'http://graph.facebook.com/' + item.id + '/picture',
                                    'label': '<img src="' + 'http://graph.facebook.com/' + item.id + '/picture"/>' +
                                        item.name,
                                    'value': item.name,
                                    'id': item.id
                                });
                            }
                        }
                        callback(results);
                    });
                },
                select: function(event, ui) {
                    var item = ui.item;
                    $('#autocomplete-items').append('<li>' +
                            '<a target="_blank" href="http://facebook.com/' + item.id + '">' +
                                item.label +
                            '</a>' +
                        '</li>'
                    );
                    $(el).closest('form').append(
                        '<input type="hidden" name="item_id" value="' + item.id + '"/>'
                    );
                    $(el).closest('form').append(
                        '<input type="hidden" name="item_' + item.id + '_name" value="' + item.value + '"/>'
                    );
                    $(el).autocomplete('close');
                    $(el).val('');
                    return false;
                },
                minLength: 2
            }).data("autocomplete")._renderItem = function( ul, item ) {
                return $("<li></li>")
                    .data("item.autocomplete", item)
                    .append("<a>"+ item.label + "</a>")
                    .appendTo(ul);
            };
        },
        loadFriendsActivityFeed: function(user_id, item_id, category) {
            if (user_id === undefined)
                user_id = 0;
            if (item_id === undefined)
                item_id = 0;
            var url = '/friends-activity-feed/' + user_id + '/' + item_id
                 + '/?category=' + category;
            $.getJSON(url, function(response) {
                $('#user-activity-feed').empty();
                for (var i in response.feed) {
                    var item = response.feed[i];
                    $('#user-activity-feed').append('<li>' +
                          '<a href="/users/' + item.user_id + '/movies/"><img src="' + item.user_image + '/></a>' +
                          '<p>' +
                            '<a href="#">' + item.user_name + '</a> ' +
                            item.action_name +
                            ' <a href="' +
                                (item.item_link?item.item_link:'#') +
                            '">' + item.item_name + '</a>' +
                          '</p>' +
                          '<p class="date">' +
                            '<abbr class="timeago" title="' + item.created + '">' +
                              item.created +
                            '</abbr>' +
                          '</p>' +
                        '</li>'
                    );
                }
                $("abbr.timeago").timeago();
            });
        },
        loadUserActivityFeed: function(user_id, item_id, category) {
            if (user_id === undefined)
                user_id = 0;
            if (item_id === undefined)
                item_id = 0;
            var url = '/user-activity-feed/' + user_id + '/' + item_id
                 + '/?category=' + category;
            $.getJSON(url, function(response) {
                $('#user-activity-feed').empty();
                for (var i in response.feed) {
                    var item = response.feed[i];
                    $('#user-activity-feed').append('<li>' +
                          '<a href="/users/' + item.user_id + '/movies/"><img src="' + item.user_image + '/></a>' +
                          '<p>' +
                            '<a href="#">' + item.user_name + '</a> ' +
                            item.action_name +
                            ' <a href="' +
                                (item.item_link?item.item_link:'#') +
                            '">' + item.item_name + '</a>' +
                          '</p>' +
                          '<p class="date">' +
                            '<abbr class="timeago" title="' + item.created + '">' +
                              item.created +
                            '</abbr>' +
                          '</p>' +
                        '</li>'
                    );
                }
                $("abbr.timeago").timeago();
            });
        }
    };
})($);
