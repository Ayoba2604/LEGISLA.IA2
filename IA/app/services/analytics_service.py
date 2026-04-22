from collections import Counter
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db.repositories.analytics import AnalyticsRepository


class AnalyticsService:
    def __init__(self, db: Session):
        self.repo = AnalyticsRepository(db)

    def record_event(
        self,
        *,
        tipo: str,
        rota: str | None = None,
        detalhe: str | None = None,
        user_id: int | None = None,
    ) -> None:
        self.repo.create_event(tipo=tipo, rota=rota, detalhe=detalhe, user_id=user_id)

    def build_dashboard_metrics(self, days: int = 7) -> dict:
        today = datetime.now()
        start_date = (today - timedelta(days=days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
        events = self.repo.list_events_since(start_date)

        day_keys = [(start_date + timedelta(days=offset)).date() for offset in range(days)]
        daily_map = {
            key: {
                'page_view': 0,
                'login': 0,
                'admin_action': 0,
                'register': 0,
                'routes': Counter(),
                'hours': [
                    {
                        'hour': hour,
                        'label': f'{hour:02d}:00',
                        'page_view': 0,
                        'login': 0,
                        'admin_action': 0,
                        'register': 0,
                        'total_requests': 0,
                    }
                    for hour in range(24)
                ],
            }
            for key in day_keys
        }

        route_counter = Counter()
        event_counter = Counter()

        for event in events:
            day_key = event.criado_em.date()
            if day_key not in daily_map:
                continue

            if event.tipo in daily_map[day_key]:
                daily_map[day_key][event.tipo] += 1

            hour_bucket = daily_map[day_key]['hours'][event.criado_em.hour]
            if event.tipo in hour_bucket:
                hour_bucket[event.tipo] += 1
            hour_bucket['total_requests'] += 1

            if event.rota:
                route_counter[event.rota] += 1
                daily_map[day_key]['routes'][event.rota] += 1

            event_counter[event.tipo] += 1

        return {
            'summary': {
                'page_views': event_counter['page_view'],
                'logins': event_counter['login'],
                'admin_actions': event_counter['admin_action'],
                'registers': event_counter['register'],
            },
            'daily': [
                {
                    'date': key.isoformat(),
                    'label': key.strftime('%d/%m'),
                    'day': key.day,
                    'month': key.month,
                    'year': key.year,
                    'page_views': values['page_view'],
                    'logins': values['login'],
                    'admin_actions': values['admin_action'],
                    'registers': values['register'],
                    'total_events': values['page_view'] + values['login'] + values['admin_action'] + values['register'],
                    'hours': [
                        {
                            'hour': hour_entry['hour'],
                            'label': hour_entry['label'],
                            'page_views': hour_entry['page_view'],
                            'logins': hour_entry['login'],
                            'admin_actions': hour_entry['admin_action'],
                            'registers': hour_entry['register'],
                            'total_requests': hour_entry['total_requests'],
                        }
                        for hour_entry in values['hours']
                    ],
                    'top_route': (
                        {'route': values['routes'].most_common(1)[0][0], 'count': values['routes'].most_common(1)[0][1]}
                        if values['routes']
                        else None
                    ),
                }
                for key, values in daily_map.items()
            ],
            'top_routes': [
                {'route': route, 'count': count}
                for route, count in route_counter.most_common(5)
            ],
        }
