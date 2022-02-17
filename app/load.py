from datetime import datetime

from app.models import Dish, PurchaseOrder, Restaurant, Schedule, User, db


def parse_time_span(time_string):
    """
    Parse a time range from a string like "10:30am-11:20pm".

    If the closing time is lesser than opening time, `overnight` is
    returned as `True`. This would tell that time spans more than a day.

    >>> parse_time_span("10:30am-11:20pm)
    (datetime.time(10, 30), datetime.time(11, 20), False)
    >>> parse_time_span(10, 0), datetime.time(2, 30), True)
    """

    def strptime(dt):
        try:
            # Try parsing with minutes like 10:30am in 24 hour format.
            return datetime.strptime(dt, "%I:%M%p").time()
        except ValueError:
            # Try parsing without minutes like datetime.time(10, 0)
            return datetime.strptime(dt, "%I%p").time()

    opens_at, closes_at = time_string.split("-")
    opens_at, closes_at = strptime(opens_at), strptime(closes_at)
    overnight = closes_at < opens_at  # True if closing time is less than opening time.
    return opens_at, closes_at, overnight


def parse_weekday(weekday_string):
    """Return a number from 0-6 representing the current weekday"""
    return {
        "MON": 0,
        "TUES": 1,
        "WEDS": 2,
        "WED": 2,
        "THU": 3,
        "THURS": 3,
        "FRI": 4,
        "SAT": 5,
        "SUN": 6,
    }.get(weekday_string.upper())


def week_iter(start, end):
    """
    Return a circular range, ranging from 0-6 such that the loop resets
    back to zero after reaching 6. This is done so that range like
    'Sun-Tue' (6-2) is parsed correctly.

    >> week_iter(6-2)
    [6, 0, 1, 2]
    >> week_iter(3, 1)
    [3, 4, 5, 6, 0, 1]
    """

    diff = (end - start) % 7
    r = []
    for _ in range(diff + 1):
        r.append(start % 7)
        start = start + 1
    return r


def parse_schedule(hours):
    """Return a dictionary with weekday as key and Schedule for each
    day stored as tuple (opens_at, closes_at, overnight) as value

    >>> parse_schedule(
    ...     "Mon - Tues, Wed-Fri 10 am - 11:45 am / Sat 7:45 am - 2:15 pm / "
    ...     "Sun 11:15 am - 3 pm"
    ... )
    {
        0 : (time(10, 0), time(11, 45), False),
        1 : (time(10, 0), time(20, 43), False),
        1 : (time(10, 0), time(20, 43), False),
        1 : (time(10, 0), time(20, 43), False),
        1 : (time(10, 0), time(20, 43), False),
        1 : (time(10, 0), time( 2, 43),  True),

    }
    """

    def add_range(part):
        """part: "Mon - Wed" """
        weekday_start, weekday_end = [p.strip() for p in part.split("-")]
        weekday_start = parse_weekday(weekday_start)
        weekday_end = parse_weekday(weekday_end)
        for weekday in week_iter(weekday_start, weekday_end):
            schedule[weekday] = (opens_at, closes_at, overnight)

    def add_single(string):
        """part: "Mon" """
        weekday = parse_weekday(string)
        schedule[weekday] = (opens_at, closes_at, overnight)

    schedule = {}

    days = [hr.strip() for hr in hours.split("/")]
    for day in days:
        d = day.split()

        # Last 5 values of 'd' will always have the time range.

        time_string = "".join(d[-5:])
        opens_at, closes_at, overnight = parse_time_span(time_string)

        weekday_part = "".join(d[:-5])
        groups = weekday_part.split(",")
        for group in groups:
            if "-" in group:
                add_range(group)
            else:
                add_single(group.strip())
    return schedule


def add_users(data):
    """Add all the users and purchase orders from `data` to database"""

    for user in data:
        userdb = User(name=user["name"], cash_balance=user["cashBalance"])
        db.session.add(userdb)
        db.session.commit()

        purchase_order_db = [
            PurchaseOrder(
                dish_name=order["dishName"],
                restaurant_name=order["restaurantName"],
                transaction_amount=order["transactionAmount"],
                transaction_date=datetime.strptime(
                    order["transactionDate"], "%m/%d/%Y %H:%M %p"
                ),
                user_id=userdb.id,
                restaurant_id=Restaurant.query.filter(
                    Restaurant.name == order["restaurantName"]
                )
                .one()
                .id,
            )
            for order in user["purchaseHistory"]
        ]

        db.session.bulk_save_objects(purchase_order_db)
    db.session.commit()


def add_restaurants(data):
    """Add all the restaurants, schedules and dishes from `data` to database"""
    for rest in data:
        rest_db = Restaurant(
            name=rest["restaurantName"],
            cash_balance=rest["cashBalance"],
        )
        db.session.add(rest_db)
        db.session.commit()

        menu_db = [
            Dish(
                name=dish["dishName"],
                price=dish["price"],
                restaurant_id=rest_db.id,
            )
            for dish in rest["menu"]
        ]

        db.session.bulk_save_objects(menu_db)

        schedule = parse_schedule(rest["openingHours"])
        schedule_db = [
            Schedule(
                weekday=weekday,
                opens_at=opens_at,
                closes_at=closes_at,
                overnight=overnight,
                restaurant_id=rest_db.id,
            )
            for weekday, (opens_at, closes_at, overnight) in schedule.items()
        ]

        db.session.bulk_save_objects(schedule_db)
    db.session.commit()

    # Index the newly created data with elasticsearch.
    Restaurant.reindex()
    Dish.reindex()
