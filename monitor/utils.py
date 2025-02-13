from datetime import timedelta
from django.utils import timezone
from django.apps import apps
from django.conf import settings
import requests
import logging
import traceback
import re
from monitor.models import Metric

def check_metric(server, metric_type, current_value, threshold, Incident):
    if current_value > threshold:
        active_incident = Incident.objects.filter(
            server=server,
            metric_type=metric_type,
            resolved=False
        ).first()

        if not active_incident:
            Incident.objects.create(
                server=server,
                metric_type=metric_type,
                start_time=timezone.now()
            )
        else:
            active_incident.count += 1
            active_incident.save()
    else:
        active_incident = Incident.objects.filter(
            server=server,
            metric_type=metric_type,
            resolved=False
        ).first()

        if active_incident:
            active_incident.end_time = timezone.now()
            active_incident.resolved = True
            active_incident.save()

import re
from django.core.exceptions import ValidationError
from django.conf import settings

def process_metrics(server, data, Incident):
    # Проверка наличия обязательных ключей
    required_keys = ['cpu', 'mem', 'disk', 'uptime']
    for key in required_keys:
        if key not in data:
            raise KeyError(f"Отсутствует обязательный ключ: {key}")

    # Проверка корректности значений
    try:
        # Проверка и преобразование cpu
        cpu = int(data['cpu'])
        if cpu < 0 or cpu > 100:
            raise ValueError("Значение cpu должно быть в диапазоне от 0 до 100")

        # Проверка и преобразование mem
        if not isinstance(data['mem'], str) or '%' not in data['mem']:
            raise ValueError("Значение mem должно быть строкой с символом %")
        data['mem'] = mem = int(re.sub(r'%', '', data['mem']))
        if mem < 0 or mem > 100:
            raise ValueError("Значение mem должно быть в диапазоне от 0 до 100")

        # Проверка и преобразование disk
        if not isinstance(data['disk'], str) or '%' not in data['disk']:
            raise ValueError("Значение disk должно быть строкой с символом %")
        data['disk'] = disk = int(re.sub(r'%', '', data['disk']))
        if disk < 0 or disk > 100:
            raise ValueError("Значение disk должно быть в диапазоне от 0 до 100")


    except ValueError as e:
        raise ValueError(f"Некорректное значение: {e}")

    # Создание записи в базе данных
    Metric.objects.create(
        server=server,
        cpu=cpu,
        mem=mem,
        disk=disk,
        uptime=data['uptime']
    )

    # Проверка метрик на превышение пороговых значений
    for metric_type, threshold in settings.METRICS.items():
        value = data[metric_type]
        current_value = int(value)
        check_metric(server, metric_type, current_value, threshold, Incident)

def fetch_metrics():
    Server = apps.get_model('monitor', 'Server')
    Metric = apps.get_model('monitor', 'Metric')
    Incident = apps.get_model('monitor', 'Incident')

    servers = Server.objects.all()
    for server in servers:
        try:
            response = requests.get(server.endpoint, timeout=10)

            if response.ok:
                data = response.json()
                process_metrics(server, data, Incident)

        except requests.exceptions.Timeout:
            logging.error(f"Timeout while polling {server.endpoint}")
        except Exception as e:
            logging.error(f"Error polling {server.endpoint}: {str(e)}")

def fetch_metrics_for_test(metrics, val):
    Server = apps.get_model('monitor', 'Server')
    Metric = apps.get_model('monitor', 'Metric')
    Incident = apps.get_model('monitor', 'Incident')

    servers = Server.objects.all()
    for server in servers:
        try:
            response = requests.get(server.endpoint + f'/met/{metrics}/{val}', timeout=10)

            if response.ok:
                data = response.json()
                process_metrics(server, data, Incident)

        except Exception as e:
            logging.error(f"Ошибка опроса {server.endpoint}: {str(e)}")
            logging.error(traceback.format_exc())



