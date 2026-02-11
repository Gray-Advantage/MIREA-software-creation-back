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
pip install -r requirements/dev.txt 
```
