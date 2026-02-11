# <Название>


## Установка и развёртывание

1. Клонируем репозиторий и переходим в проект
```bash
git clone <URL> <project>
cd <project>
```

2. Создаём виртуальную среду и активируем
```bash
python3 -m venv venv      # Linux/MacOS
source venv/bin/activate  # Linux/MacOS

python -m venv venv       # Windows
.\venv\Scripts\activate   # Windows
```

3. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements/dev.txt 
```

4. Создание `.env` файла
```bash
cp .env.example .env    # Linux/MacOS
copy .env.example .env  # Windows
```

После поменять настройки в `.env` под себя
