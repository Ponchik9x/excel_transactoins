import datetime
import os
import re
from typing import Any

import pandas as pd
import requests
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

load_dotenv(".env")


def read_file_exel(file_gate: str) -> list[dict | dict]:
    """Принимает на вход путь к файлу .exel и возвращает список словарей из файла"""
    returned_list = []
    try:
        df = pd.read_excel(file_gate)
        df = df.loc[df.Статус.notnull()]
        returned_list = df.to_dict(orient="records")
    except ValueError:
        print("Неверный адрес")
    finally:
        return returned_list


def mask_card(card_name: str) -> str:
    """Функция для вывода последних 4 цифв карты.
    Принимает тип и номер карты(str).
    Возвращает последние 4 цифры(str)"""
    pattern_num = r"\d+"
    card_number = re.finditer(pattern_num, card_name)
    encrypted_card = ""
    for num in card_number:
        encrypted_card = f"{num.group()[-4:]}"

    return encrypted_card


def get_unique_card_number(list_of_transactions: list[dict | dict]) -> list[str | int]:
    """Функция для вывода списка количества карт.
    Принимает список словарей транзакций.
    Возвращает список номеров карт"""
    unique_card_num = []
    for d in list_of_transactions:
        if isinstance(d["Номер карты"], str | int):
            if d["Номер карты"] not in unique_card_num:
                unique_card_num.append(d["Номер карты"])
    return unique_card_num


def get_total_expenses(list_of_transactions: list[dict | dict], card_number: str) -> float:
    """Функция считает общую сумму расходов по списку операций по карте.
    Принимает список операций по карте.
    Возвращает общую сумму расходов."""
    total_expenses = 0.00
    for d in list_of_transactions:
        if d["Номер карты"] == card_number:
            total_expenses += float(d["Сумма операции с округлением"])
    return round(total_expenses, 2)


def get_top_transactions(list_of_transactions: list[dict | dict]) -> list[dict]:
    """Функция сортирует список словарей по убыванию (reverse_list_dict = True) и
    получает топ-5 транзакций по сумме платежа.
    Принимает лист транзакций.
    Возвращает список транзакций."""
    sort_by_date_dict = sorted(list_of_transactions, reverse=True, key=lambda item: item["Дата операции"])
    top_five_transactions = sort_by_date_dict[:5]

    return top_five_transactions


def get_date(date_: str) -> str:
    """Функция возвращает строку с датой в формате "ДД.ММ.ГГГГ"("11.03.2024").
    :param date_: datetime:
    """
    split_date = date_.split()
    return split_date[0]


def get_currency_rates() -> tuple[dict[str, str | Any], dict[str, str | Any]]:
    """Функция делает запрос на exchangerates_data-api.
    Возвращает два словаря с актуальными значениями EUR и USD
    """

    url_eur_to_rub = "https://api.apilayer.com/exchangerates_data/latest?symbols=RUB&base=EUR"

    url_usd_to_rub = "https://api.apilayer.com/exchangerates_data/latest?symbols=RUB&base=USD"

    headers = {"apikey": f"{os.getenv('API_LAYER_KEY')}"}
    payload_eur = {}
    response_eur = requests.request("GET", url_eur_to_rub, headers=headers, data=payload_eur)
    payload_usd = {}
    response_usd = requests.request("GET", url_usd_to_rub, headers=headers, data=payload_usd)

    result_eur = response_eur.json()
    result_usd = response_usd.json()

    result = {"currency": "USD", "rate": result_usd["rates"]["RUB"]}, {
        "currency": "EUR",
        "rate": result_eur["rates"]["RUB"],
    }

    return result


def get_stock_price():
    """

    :return:
    """
    stocks_list = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    price_stocks = []

    api_key_twelvedata = f"{os.getenv('API_TWELVE_DATA')}"

    for stock in stocks_list:
        response = requests.get(f"https://api.twelvedata.com/price?symbol={stock}&apikey={api_key_twelvedata}")
        dict_result = response.json()
        price_element = dict_result.get("price")
        price_stocks.append(price_element)


def get_result_list_from_date(date_str, delta_date: str = "M"):
    """qwe"""
    date = datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    file = read_file_exel("data/operations.xlsx")

    if delta_date == "W":
        start_date = date - relativedelta(weeks=1)
        end_date = date
    elif delta_date == "M":
        start_date = date.replace(day=1)
        end_date = date
    elif delta_date == "Y":
        start_date = date - relativedelta(years=1)
        end_date = date
    elif delta_date == "ALL":
        start_date = datetime.datetime(2000, 1, 1, 0, 0, 00)
        end_date = date
    else:
        raise ValueError("Некорректный диапазон данных.")

    result_list = []

    for v in file:
        v["Дата операции"] = datetime.datetime.strptime(v["Дата операции"], "%d.%m.%Y %H:%M:%S")
        if v["Дата операции"].year == 2021:
            v["Дата операции"].replace(year=2025)
        if start_date <= v["Дата операции"] <= end_date:
            result_list.append(v)

    return result_list


def total_amount_from_list(list_dicts: list[dict | dict]) -> float:
    """

    :param list_dicts:
    :return:
    """
    total_amount = 0.0
    for v in list_dicts:
        total_amount += v["Сумма операции с округлением"]
    return total_amount


def get_total_income(data_frame_list):
    """

    :param data_frame_list:
    :return:
    """
    income_by_category = (
        data_frame_list[data_frame_list["Сумма операции"] > 0]
        .groupby("Категория")["Сумма операции"]
        .sum()
        .reset_index()
    )
    income_by_category["Сумма операции"] = income_by_category["Сумма операции"].round(0)

    total_sum_income = income_by_category["Сумма операции"].sum()

    return total_sum_income


def list_pd_income(data_frame_list):
    """Группирует поступления по категориям и возвращает основные категории и их сумму."""
    income_by_category = (
        data_frame_list[data_frame_list["Сумма операции"] > 0]
        .groupby("Категория")["Сумма операции"]
        .sum()
        .reset_index()
    )
    income_by_category["Сумма операции"] = income_by_category["Сумма операции"].round(0)
    top_income = income_by_category.nlargest(3, "Сумма операции")

    combined_income = pd.concat([top_income], ignore_index=True)

    return combined_income


def list_pd_outcome(filtered_list):
    """weqweqe"""
    income_by_category = (
        filtered_list[filtered_list["Сумма операции"] < 0].groupby("Категория")["Сумма операции"].sum().reset_index()
    )

    income_by_category["Сумма операции"] = income_by_category["Сумма операции"].round(0) * -1

    top_income = income_by_category.nlargest(7, "Сумма операции")
    other_income_sum = income_by_category.loc[
        income_by_category["Категория"].isin(top_income["Категория"]), "Сумма операции"
    ].sum()

    other_income = pd.DataFrame({"Категория": ["Остальное"], "Сумма операции": [other_income_sum]})

    combined_income = pd.concat([top_income, other_income], ignore_index=True)

    return combined_income


def list_pd_outcome_transfers_and_cash(data_frame_list):
    """weqweqe"""
    income_by_category = (
        data_frame_list[data_frame_list["Сумма операции"] < 0]
        .groupby("Категория")["Сумма операции"]
        .sum()
        .reset_index()
    )

    income_by_category["Сумма операции"] = income_by_category["Сумма операции"].round(0) * -1

    cash_frame = income_by_category.loc[income_by_category["Категория"] == "Наличные"]

    transfers_frame = income_by_category.loc[income_by_category["Категория"] == "Переводы"]

    combined_income = pd.concat([cash_frame, transfers_frame], ignore_index=True)

    return combined_income


operations_path = os.path.join("data/operations.xlsx")
file_pd = pd.read_excel(operations_path)
