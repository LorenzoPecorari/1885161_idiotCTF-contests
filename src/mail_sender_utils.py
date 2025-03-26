import redis
import json

class MailSender:
    def __init__(self, queue_name="email_queue", redis_host='redis', redis_port=6379):
        self.queue_name = queue_name
        self.redis_client = redis.StrictRedis(host=redis_host, port=redis_port, decode_responses=True)

    def user_notification(self, email):
        email_data = {
            "to_email": email,
            "subject": "Contest Subscription",
            "body": "Hi! You are now subscribed to a new contest! Please check the contest page http://127.0.0.1:3000/contests"
        }
        self.redis_client.lpush(self.queue_name, json.dumps(email_data))
        print(email_data)

# Example usage:
# mail_sender = MailSender()
# mail_sender.user_notification("example@example.com")