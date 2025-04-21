import datetime
import json
import logging
import os

import pandas as pd
import requests
from dotenv import load_dotenv

from utils import (get_date, get_result_list_from_date, get_top_transactions, get_total_expenses, get_total_income,
                   get_unique_card_number, list_pd_income, list_pd_outcome, list_pd_outcome_transfers_and_cash,
                   mask_card, read_file_exel, total_amount_from_list)

load_dotenv(".env")


logger = logging.getLogger("views")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler("logs/views.log", mode="w")
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


datetime_today = datetime.datetime.now()
formatted_date = datetime_today.strftime("%Y-%m-%d %H:%M:%S")

formatted_date = formatted_date[:3] + "1" + formatted_date[4:]


def generate_json_greeting_head(data_str: str) -> str:
    """Основная функция для главной страницы.
    Принимает на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS
    Возвращает JSON-ответ
    Использованы библиотеки: json, datetime, logging, pandas
    """
    logger.info("Чтение файла")

    file = read_file_exel("data/operations.xlsx")

    logger.info("Преобразование даты в формат datetime")

    id_datatime = datetime.datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")

    my_dict: dict[str, list | str] = {
        "greeting": "",
        "cards": [],
        "top_transactions": [],
        "currency_rates": [],
        "stock_prices": [],
    }

    greeting = {"morning": "Доброе утро", "day": "Добрый день", "evening": "Добрый вечер", "night": "Доброй ночи"}

    logger.info("Определение времени суток")

    if id_datatime.hour < 12:
        my_dict["greeting"] = greeting["morning"]
    elif id_datatime.hour < 17:
        my_dict["greeting"] = greeting["day"]
    elif id_datatime.hour < 22:
        my_dict["greeting"] = greeting["evening"]
    else:
        my_dict["greeting"] = greeting["night"]

    logger.info("Получение списка карт")

    unique_card = get_unique_card_number(file)

    logger.info("Добавление значений по ключу my_dict['cards']")

    for card in unique_card:
        last_digits = mask_card(card)
        cashback = round(get_total_expenses(file, card) / 100, 2)
        total_expenses_from_card = get_total_expenses(file, card)
        my_dict["cards"].append(
            {"last_digits": last_digits, "total_spent": total_expenses_from_card, "cashback": cashback}
        )

    logger.info("Добавление значений по ключу my_dict['top_transactions']")

    for d in get_top_transactions(file):
        need_dict = {
            "date": get_date(d["Дата операции"]),
            "amount": d["Сумма операции с округлением"],
            "category": d["Категория"],
            "description": d["Описание"],
        }
        my_dict["top_transactions"].append(need_dict)

    logger.info("Получение курса валют по API KEY")

    url_eur_to_rub = "https://api.apilayer.com/exchangerates_data/latest?symbols=RUB&base=EUR"
    url_usd_to_rub = "https://api.apilayer.com/exchangerates_data/latest?symbols=RUB&base=USD"

    headers_layer = {"apikey": f"{os.getenv('API_LAYER_KEY')}"}

    response_eur = requests.request("GET", url_eur_to_rub, headers=headers_layer)
    response_usd = requests.request("GET", url_usd_to_rub, headers=headers_layer)

    result_eur = response_eur.json()
    result_usd = response_usd.json()

    my_dict_usd = {"currency": "USD", "rate": result_usd["rates"]["RUB"]}
    my_dict_eur = {"currency": "EUR", "rate": result_eur["rates"]["RUB"]}

    logger.info("Добавление значений по ключу my_dict['currency_rates']")

    my_dict["currency_rates"].append(my_dict_usd)
    my_dict["currency_rates"].append(my_dict_eur)

    logger.info("Получение стоимости акций по списку и по API KEY")

    stocks_list = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]

    headers_twelve_data = f"{os.getenv('API_TWELVE_DATA')}"

    logger.info("Добавление значений по ключу my_dict['stock_prices']")

    for stock in stocks_list:
        response = requests.get(f"https://api.twelvedata.com/price?symbol={stock}&apikey={headers_twelve_data}")
        dict_result = response.json()
        price_element = {"stock": stock, "price": dict_result.get("price")}
        my_dict["stock_prices"].append(price_element)

    logger.info("Возвращение словаря с данными")

    result = json.dumps(my_dict)

    return result


def generate_json_greeting_(date_str: str, delta_date: str = "M") -> str:
    """Функция для страницы «События».
    Функция принимает на вход DataFrame.
    Возвращает JSON-ответ.
    Вспомогательные функции расположены в модуле utils.py.
    """

    operations_path = os.path.join("data/operations.xlsx")
    file_pd = pd.read_excel(operations_path)

    filtered_list_by_date = get_result_list_from_date(date_str, delta_date)

    my_dict = {
        "expenses": {"total_amount": 0.0, "main": [], "transfers_and_cash": []},
        "income": {"total_amount": 0.0, "main": []},
        "currency_rates": [],
        "stock_prices": [],
    }

    total_amount_outcome = total_amount_from_list(filtered_list_by_date)
    my_dict["expenses"]["total_amount"] = round(total_amount_outcome, 2)

    my_list_outcome = list_pd_outcome(file_pd).to_dict(orient="records")
    for v in my_list_outcome:
        my_dict["expenses"]["main"].append({"category": f"{v['Категория']}", "amount": f"{v['Сумма операции']}"})

    my_list_outcome_transfers_and_cash = list_pd_outcome_transfers_and_cash(file_pd).to_dict(orient="records")
    for v in my_list_outcome_transfers_and_cash:
        my_dict["expenses"]["transfers_and_cash"].append(
            {"category": f"{v['Категория']}", "amount": f"{v['Сумма операции']}"}
        )

    my_list_income = list_pd_income(file_pd).to_dict(orient="records")
    for v in my_list_income:
        my_dict["income"]["main"].append({"category": f"{v['Категория']}", "amount": f"{v['Сумма операции']}"})

    total_sum_income = float(get_total_income(file_pd))

    my_dict["income"]["total_amount"] = total_sum_income

    url_eur_to_rub = "https://api.apilayer.com/exchangerates_data/latest?symbols=RUB&base=EUR"
    url_usd_to_rub = "https://api.apilayer.com/exchangerates_data/latest?symbols=RUB&base=USD"

    headers_layer = {"apikey": f"{os.getenv('API_LAYER_KEY')}"}

    response_eur = requests.request("GET", url_eur_to_rub, headers=headers_layer)
    response_usd = requests.request("GET", url_usd_to_rub, headers=headers_layer)

    result_eur = response_eur.json()
    result_usd = response_usd.json()
    my_dict_usd = {"currency": "USD", "rate": result_usd["rates"]["RUB"]}
    my_dict_eur = {"currency": "EUR", "rate": result_eur["rates"]["RUB"]}
    my_dict["currency_rates"].append(my_dict_usd)
    my_dict["currency_rates"].append(my_dict_eur)

    stocks_list = ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"]
    headers_twelve_data = f"{os.getenv('API_TWELVE_DATA')}"
    for stock in stocks_list:
        response = requests.get(f"https://api.twelvedata.com/price?symbol={stock}&apikey={headers_twelve_data}")
        dict_result = response.json()
        price_element = {"stock": stock, "price": dict_result.get("price")}
        my_dict["stock_prices"].append(price_element)

    result = json.dumps(my_dict)

    return result
