from tornado import gen
from datetime import datetime


class ActivityMixin(object):

    @gen.engine
    def track_activity(
        self, user_id, user_name, action_id, action_name, item_id, item_name,
        user_link=None, item_link=None, user_image=None, item_image=None,
        category=None, callback=None
    ):
        yield gen.Task(
            self.async_db.activity.insert,
            {
                'user_id': user_id,
                'user_name': user_name,
                'action_id': action_id,
                'action_name': action_name,
                'item_id': item_id,
                'item_name': item_name,
                'user_link': user_link,
                'item_link': item_link,
                'user_image': user_image,
                'item_image': item_image,
                'created': datetime.now(),
                'category': category
            }
        )
        if callback:
            callback()
