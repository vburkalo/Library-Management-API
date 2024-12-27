import unittest
from unittest.mock import patch, MagicMock

from borrowings.notifications import notify_new_borrowing


class TestNotifyNewBorrowing(unittest.TestCase):
    @patch("borrowings.notifications.send_notification")
    async def test_notify_new_borrowing(self, mock_send_notification):
        borrowing = MagicMock()
        chat_id = "6976462510"
        message = f"New borrowing created: {borrowing}"

        await notify_new_borrowing(borrowing)

        mock_send_notification.assert_called_once_with(chat_id, message)


if __name__ == "__main__":
    unittest.main()
