import json
import logging
import os
from datetime import datetime
from typing import Any, Optional

import pandas as pd
from dateutil.relativedelta import relativedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_report(filename: Any = None) -> Any:
    """Декоратор для записи отчета в файл."""

    def wrapper(func: Any) -> Any:
        def inner(*args, filename: Optional[str] = None, **kwargs) -> Any:
            print("Функция inner:", inner)
            result = func(*args, **kwargs)
            print("Аргументы функции:", args, kwargs)
            # Имя файла по умолчанию
            if filename is None:
                file_name = f"report_{func.__name__}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            # Сохранение результата в файл
            logger.info("Сохранение результата в файл data/file")
            if not os.path.exists("data"):
                os.makedirs("data")
            file_path = f"data/{file_name}"
            print("file_path", file_path)

            def save_to_file(data, file_path):
                with open(file_path, "w", encoding="utf-8") as file:
                    json.dump(data, file, ensure_ascii=False, indent=4)

            # if not os.path.exists('data'):
            #     os.makedirs('data')# проверка, что директория существует

            save_to_file(result, file_path)

            print(save_to_file)
            print("Результат функции:", result)
            return result

        return inner

    return wrapper


def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Функция принимает на вход:
    :param transactions: датафрейм с транзакциями,
    :param category: название категории,
    :param date: опциональную дату.
    Если дата не передана, то берется текущая дата.
    :return: Функция возвращает траты по заданной категории за последние три месяца (от переданной даты)
    """
    if not date:
        date = datetime.now().date()

    try:
        start_date = pd.to_datetime(date, dayfirst=True) - relativedelta(months=3)
        end_date = pd.to_datetime(date, dayfirst=True)

    except ValueError:
        raise ValueError("Некорректная дата. Используйте формат: dd.mm.yyyy")

    transactions["Дата операции"] = pd.to_datetime(
        transactions["Дата операции"], format="%d.%m.%Y %H:%M:%S", errors="coerce"
    )

    filtered_transactions = transactions[transactions["Категория"] == category]

    filtered_transactions_to_date = filtered_transactions[
        (filtered_transactions["Дата операции"] >= start_date) & (filtered_transactions["Дата операции"] <= end_date)
    ]

    return filtered_transactions_to_date


if __name__ == "__main__":

    file = pd.read_excel("data/operations.xlsx")
    print(spending_by_category(file, "Супермаркеты", "2019-03-03"))
