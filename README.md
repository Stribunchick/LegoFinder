# LegoFinder

## Описание

LegoFinder — это локальное приложение на Python для поиска и распознавания Lego-деталей с помощью компьютеpного зрения. .

## Требования

- Windows 10/11 или Linux
- Python 3.10+ (рекомендуется 3.11)
- Git

## Подготовка окружения

1. Откройте терминал (PowerShell на Windows).
2. Перейдите в рабочую папку:
   ```powershell
   cd C:\Users\<ваш-пользователь>\Desktop
   ```
3. Клонируйте репозиторий:
   ```powershell
   git clone https://github.com/Stribunchick/LegoFinder.git
   cd LegoFinder
   ```
4. Создайте виртуальное окружение:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

## Установка зависимостей

1. Обновите pip:
   ```powershell
   python -m pip install --upgrade pip
   ```
2. Установите зависимости из `requirements.txt`:
   ```powershell
   pip install -r requirements.txt
   ```

> Если в `requirements.txt` нет нужных библиотек для `cv_pipeline`, установите их вручную:
> ```powershell
> pip install opencv-python numpy
> ```

## Запуск приложения

Из корня проекта запустите:
   ```powershell
   python app.py
   ```
## Графический интерфейс

## Обработка видеопотока



## Проверка

1. Убедитесь, что все зависимости установлены:
   ```powershell
   pip list
   ```
2. Запустите тестовый сценарий (если есть):
   ```powershell
   python -m pytest
   ```

## Траблшутинг

- Если `ModuleNotFoundError`, проверьте, что виртуальное окружение активно.
- Если OpenCV не работает, пробуйте `pip install opencv-python-headless`.
- При ошибках GUI убедитесь в наличие `PyQt5` либо `PySide6`.
