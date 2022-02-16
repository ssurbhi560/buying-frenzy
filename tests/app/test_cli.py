from unittest import mock

from app import seed_db
from app.models import Restaurant


@mock.patch("app.load.add_restaurants")
@mock.patch("app.load.add_users")
def test_seed_db(mocked_load_users, mocked_load_restaurants, app, db):
    runner = app.test_cli_runner()
    with mock.patch("requests.get") as mocked_get:
        data = [{"cashBalance": "1", "restaurantName": "ABCD", "menu": []}]
        mocked_get.return_value.json.return_value = data
        result = runner.invoke(seed_db)

    assert "Adding data to database..." in result.output
    assert "Done" in result.output
    mocked_load_restaurants.assert_called_once_with(data)
    mocked_load_users.assert_called_once_with(data)
