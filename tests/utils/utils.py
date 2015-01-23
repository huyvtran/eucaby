import json

def assert_object(obj, **kwargs):
    for k, v in kwargs.items():
        value = getattr(obj, k)
        try:
            assert v == value
        except AssertionError:
            raise ValueError('Value {} does not match {}'.format(v, value))


def verify_email(messages, num, mail_to, in_list):
    """Verifies email message.

    Args:
        message: EmailMessage object
        num: Number of messages
        to: Mail recipient list or string for each message
        in_list: Substring list in each message
    """
    assert num == len(messages)
    if num == 1:
        mail_to, in_list = [mail_to], [in_list]
    for i in range(num):
        message = messages[i]
        mail_body = str(message.body)
        assert mail_to[i] == message.to
        for in_str in in_list[i]:
            assert in_str in mail_body


def verify_invalid_methods(client, invalid_methods, endpoint):
    """Verifies invalid methods."""
    ec_invalid_method = dict(
        message='Method not allowed', code='invalid_method')
    for method in invalid_methods:
        resp = getattr(client, method)(endpoint)
        data = json.loads(resp.data)
        assert ec_invalid_method == data
        assert 405 == resp.status_code
