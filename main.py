import psycopg2

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from abc import ABC, abstractmethod

# ORM настройка
# В будущем переделать под PostgreSQL или MSSql
engine = create_engine("postgresql://postgres:123@localhost:5433/kachalka")

Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

# Подключение к базе данных
conn = psycopg2.connect("postgresql://postgres:123@localhost:5433/kachalka")
cursor = conn.cursor()

# Модели для ORM
# Модель для сущности "Тренировочный зал"
class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)
    # Связь: один зал может иметь множество тренеров
    trainers = relationship("Trainer", back_populates="room")

    def __repr__(self):
        return f"({self.id}, '{self.name}', '{self.location}', {self.capacity})"

# Модель для сущности "Тренер"
class Trainer(Base):
    __tablename__ = 'trainers'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    specialization = Column(String, nullable=False)
    experience_years = Column(Integer)
    room_id = Column(Integer, ForeignKey('rooms.id'))
    # Связь: каждый тренер связан только с одним залом
    room = relationship("Room", back_populates="trainers")

    def __repr__(self):
        return f"({self.id}, '{self.name}', '{self.specialization}', {self.experience_years}, {self.room_id})"

# Модель для сущности "Спортивное оборудование"
class Equipment(Base):
    __tablename__ = 'equipment'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)

    def __repr__(self):
        return f"({self.id}, '{self.name}', '{self.type}', {self.quantity})"

# Модель для сущности "Оборудование закреплённое за тренером"
class TrainerEquipment(Base):
    # Составной первичный ключ для обеспечения уникальности пар значений 
    # trainer-equipment
    __tablename__ = 'trainer_equipment'
    trainer_id = Column(Integer, ForeignKey('trainers.id'), primary_key=True)
    equipment_id = Column(Integer, ForeignKey('equipment.id'), primary_key=True)
    quantity = Column(Integer, nullable=False)

    def __repr__(self):
        return f"({self.trainer_id}, {self.equipment_id}, {self.quantity})"

# Задание 3
# Интерфейсы с методами для реализации задач из второго задания
# 1. Интерфейс для управления тренерами
class TrainerManagementBase(ABC):
    @abstractmethod
    def add_trainer(self, name, specialization, experience_years, room_id):
        pass

    @abstractmethod
    def update_trainer_room(self, trainer_id, new_room_id):
        pass

    @abstractmethod
    def update_trainer_spec(self, trainer_id, new_specialization):
        pass

    @abstractmethod
    def delete_trainer(self, trainer_id):
        pass

    @abstractmethod
    def select_trainers_by_room(self, room_id):
        pass

# 2. Интерфейс для управления оборудованием
class EquipmentManagementBase(ABC):
    @abstractmethod
    def add_equipment(self, name, type, quantity):
        pass

    @abstractmethod
    def add_equipment_to_trainer(self, trainer_id, equipment_id, quantity):
        pass

    @abstractmethod
    def calculate_trainer_equipment(self, trainer_id):
        pass
    
    @abstractmethod
    def calculate_all_trainer_equipment(self):
        pass

# 3. Интерфейс для управления залами
class RoomManagementBase(ABC):
    @abstractmethod
    def add_room(self, name, location, capacity):
        pass

    @abstractmethod
    def delete_room(self, room_id):
        pass

# Реализации интерфейсов с решением поставленных задач через SQLAlchemy ORM
class TrainerManagementORM(TrainerManagementBase):
    def add_trainer(self, name, specialization, experience_years, room_id):
        # Создаём экземпляр класса Trainer
        new_trainer = Trainer(name=name, specialization=specialization, experience_years=experience_years, room_id=room_id)
        # Добавляем его в БД
        session.add(new_trainer)
        session.commit()

    def update_trainer_room(self, trainer_id, new_room_id):
        # Ищем тренера по Id
        trainer = session\
                    .query(Trainer)\
                    .filter(Trainer.id == trainer_id)\
                    .first()
        # Если находим тренера, то меняем его зал
        if trainer:
            trainer.room_id = new_room_id
            session.commit()
    
    def update_trainer_spec(self, trainer_id, new_specialization):
        # Ищем тренера по Id
        trainer = session\
                    .query(Trainer)\
                    .filter(Trainer.id == trainer_id)\
                    .first()
        # Если находим тренера, то меняем его специализацию
        if trainer:
            trainer.specialization = new_specialization
            session.commit()
    
    def delete_trainer(self, trainer_id):
        # Ищем тренера по Id
        trainer = session\
                    .query(Trainer)\
                    .filter(Trainer.id == trainer_id)\
                    .first()
        # Если находим тренера, то удаляем запись о нём
        if trainer:
            session.delete(trainer)
            session.commit()

    def select_trainers_by_room(self, room_id):
        # Поиск всех тренеров, у которых зал соответсвует переданному параметру
        trainers = session\
                    .query(Trainer)\
                    .filter(Trainer.room_id == room_id)\
                    .all()
        return trainers
            
class EquipmentManagementORM(EquipmentManagementBase):
    def add_equipment(self, name, type, quantity):
        # Создаём экземпляр класса Equipment
        new_equipment = Equipment(name=name, type=type, quantity=quantity)
        session.add(new_equipment)
        # Добавляем его в БД
        session.commit()

    def add_equipment_to_trainer(self, trainer_id, equipment_id, quantity):
        # Ищем запись о закреплённом за тренером оборудовании
        existing_entry = session\
                            .query(TrainerEquipment)\
                            .filter_by(trainer_id=trainer_id, equipment_id=equipment_id)\
                            .first()
        # Если запись найдена, то суммируем поле quantity с переданным значением
        if existing_entry:
            # Изменения данных в записи отслеживаются
            existing_entry.quantity += quantity
        # Иначе создаём новую запись в БД
        else:
            new_trainer_equipment = TrainerEquipment(trainer_id=trainer_id, equipment_id=equipment_id, quantity=quantity)
            session.add(new_trainer_equipment)
        # Сохраняем изменения в БД
        session.commit()

    def calculate_trainer_equipment(self, trainer_id):
        # Ищем все записи для тренера об используемом им оборудовании
        equipment_list = session\
                            .query(TrainerEquipment, Equipment)\
                            .join(Equipment, TrainerEquipment.equipment_id == Equipment.id)\
                            .filter(TrainerEquipment.trainer_id == trainer_id)\
                            .all()
        # Объявляем словарь для хранения результата
        total_equipment = {}
        for te, eq in equipment_list:
            # Ключ - наименование единицы оборудования, Значение - количество оборудования за тренером
            total_equipment[eq.name] = te.quantity
        # Возвращаем словарь    
        return total_equipment
    
    def calculate_all_trainer_equipment(self):
        # Словарь, где ключи - ID тренера, значения - словарь с названиями оборудования и их количеством
        all_trainer_equipment = {}
        trainers = session.query(Trainer).all()  # Получаем всех тренеров из базы данных
        # Заполняем словарь
        for trainer in trainers:
            equipment_quantities = self.calculate_trainer_equipment(trainer.id)
            all_trainer_equipment[trainer.name] = equipment_quantities

        return all_trainer_equipment
    
class RoomManagementORM(RoomManagementBase):
    def add_room(self, name, location, capacity):
        # Создаём экземпляр класса Equipment
        new_room = Room(name=name, location=location, capacity=capacity)
        # Добавляем его в БД
        session.add(new_room)
        session.commit()

    def delete_room(self, room_id):
        # Ищем запись о зале по Id
        room = session\
                .query(Room)\
                .filter(Room.id == room_id)\
                .first()
        # Если находим зал, то удаляем его
        if room:
            session.delete(room)
            session.commit()

# Реализации интерфейсов с решением поставленных задач через DB API 2.0
class TrainerManagementDBAPI(TrainerManagementBase):
    def add_trainer(self, name, specialization, experience_years, room_id):
        query = "INSERT INTO trainers (name, specialization, experience_years, room_id) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (name, specialization, experience_years, room_id))
        conn.commit()

    def update_trainer_room(self, trainer_id, new_room_id):
        query = "UPDATE trainers SET room_id = %s WHERE id = %s"
        cursor.execute(query, (new_room_id, trainer_id))
        conn.commit()

    def update_trainer_spec(self, trainer_id, new_specialization):
        query = "UPDATE trainers SET specialization = %s WHERE id = %s"
        cursor.execute(query, (new_specialization, trainer_id))
        conn.commit()

    def delete_trainer(self, trainer_id):
        query = "DELETE FROM trainers WHERE id = %s"
        cursor.execute(query, (trainer_id,))
        conn.commit()

    def select_trainers_by_room(self, room_id):
        query = "SELECT * FROM trainers WHERE room_id = %s"
        cursor.execute(query, (room_id,))
        return cursor.fetchall()

class EquipmentManagementDBAPI(EquipmentManagementBase):
    def add_equipment(self, name, type, quantity):
        query = "INSERT INTO equipment (name, type, quantity) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, type, quantity))
        conn.commit()

    def add_equipment_to_trainer(self, trainer_id, equipment_id, quantity):
        # Check if entry exists
        query_check = "SELECT quantity FROM trainer_equipment WHERE trainer_id = %s AND equipment_id = %s"
        cursor.execute(query_check, (trainer_id, equipment_id))
        existing_entry = cursor.fetchone()

        if existing_entry:
            new_quantity = existing_entry[0] + quantity
            query = "UPDATE trainer_equipment SET quantity = %s WHERE trainer_id = %s AND equipment_id = %s"
            cursor.execute(query, (new_quantity, trainer_id, equipment_id))
        else:
            query = "INSERT INTO trainer_equipment (trainer_id, equipment_id, quantity) VALUES (%s, %s, %s)"
            cursor.execute(query, (trainer_id, equipment_id, quantity))
        conn.commit()


    def calculate_trainer_equipment(self, trainer_id):
        query = """
            SELECT e.name, te.quantity
            FROM trainer_equipment te
            JOIN equipment e ON te.equipment_id = e.id
            WHERE te.trainer_id = %s
        """
        cursor.execute(query, (trainer_id,))
        results = cursor.fetchall()
        total_equipment = {}
        for name, quantity in results:
            total_equipment[name] = quantity
        return total_equipment
    
    def calculate_all_trainer_equipment(self):
        # Словарь, где ключи - ID тренера, значения - словарь с названиями оборудования и их количеством
        all_trainer_equipment = {}
        trainers = session.query(Trainer).all()  # Получаем всех тренеров из базы данных
        # Заполняем словарь
        for trainer in trainers:
            equipment_quantities = self.calculate_trainer_equipment(trainer.id)
            all_trainer_equipment[trainer.name] = equipment_quantities

        return all_trainer_equipment

class RoomManagementDBAPI(RoomManagementBase):
    def add_room(self, name, location, capacity):
        query = "INSERT INTO rooms (name, location, capacity) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, location, capacity))
        conn.commit()

    def delete_room(self, room_id):
        query = "DELETE FROM rooms WHERE id = %s"
        cursor.execute(query, (room_id,))
        conn.commit()

def create_test_data(trainer_manager_orm, equipment_manager_orm, room_manager_orm, trainer_manager_dbapi, equipment_manager_dbapi, room_manager_dbapi):
    # Добавляем 2 зала с помощью ORM
    room_manager_orm.add_room("Зал бокса", "ул. Ленина, 10", 20)
    room_manager_orm.add_room("Кардио зона", "пр. Мира, 5", 30)

    # Добавляем 2 зала с помощью DBAPI
    room_manager_dbapi.add_room("Зона свободных весов", "ул. Гагарина, 15", 40)
    room_manager_dbapi.add_room("Зал групповых программ", "ул. Космонавтов, 2", 25)

    # Добавляем 3 тренера с помощью ORM
    trainer_manager_orm.add_trainer("Иванов Иван Иванович", "Бодибилдинг", 10, 1)
    trainer_manager_orm.add_trainer("Петров Петр Петрович", "Пауэрлифтинг", 5, 1)
    trainer_manager_orm.add_trainer("Сидорова Анна Сергеевна", "Фитнес", 3, 2)

    # Добавляем 3 тренера с помощью DBAPI
    trainer_manager_dbapi.add_trainer("Смирнов Алексей Иванович", "Кроссфит", 7, 2)
    trainer_manager_dbapi.add_trainer("Козлова Елена Владимировна", "Пилатес", 2, 1)
    trainer_manager_dbapi.add_trainer("Волков Дмитрий Андреевич", "TRX", 4, 2)

    # Добавляем 3 единицы оборудования с помощью ORM
    equipment_manager_orm.add_equipment("Гантели 2кг", "Силовая тренировка", 20)
    equipment_manager_orm.add_equipment("Беговая дорожка", "Кардио", 5)
    equipment_manager_orm.add_equipment("Тренажер Смита", "Силовая тренировка", 2)

    # Добавляем 3 единицы оборудования с помощью DBAPI
    equipment_manager_dbapi.add_equipment("Велотренажер", "Кардио", 3)
    equipment_manager_dbapi.add_equipment("Эллиптический тренажер", "Кардио", 4)
    equipment_manager_dbapi.add_equipment("Гиря 16кг", "Силовая тренировка", 10)

    #Привязываем оборудование к тренерам
    #trainer_id, equipment_id, quantity

    equipment_manager_orm.add_equipment_to_trainer(1, 1, 5)
    equipment_manager_orm.add_equipment_to_trainer(1, 2, 2)
    equipment_manager_orm.add_equipment_to_trainer(2, 3, 1)
    equipment_manager_orm.add_equipment_to_trainer(3, 4, 8)
    equipment_manager_orm.add_equipment_to_trainer(4, 5, 10)

    equipment_manager_dbapi.add_equipment_to_trainer(5, 1, 3)
    equipment_manager_dbapi.add_equipment_to_trainer(4, 2, 1)
    equipment_manager_dbapi.add_equipment_to_trainer(3, 3, 2)
    equipment_manager_dbapi.add_equipment_to_trainer(2, 4, 6)
    equipment_manager_dbapi.add_equipment_to_trainer(1, 5, 5)

if __name__ == '__main__':
    # Создание базы данных и таблиц, если они не существуют.
    # Для первоначальной настройки. Alembic обрабатывает последующие изменения.
    # Base.metadata.create_all(engine)

    trainer_manager_orm = TrainerManagementORM()
    equipment_manager_orm = EquipmentManagementORM()
    room_manager_orm = RoomManagementORM()

    trainer_manager_dbapi = TrainerManagementDBAPI()
    equipment_manager_dbapi = EquipmentManagementDBAPI()
    room_manager_dbapi = RoomManagementDBAPI()

    try:
        # # Проверка методов добавления записей в таблицы (тренеров, оборудования, залов)
        create_test_data(trainer_manager_orm, equipment_manager_orm, room_manager_orm, trainer_manager_dbapi, equipment_manager_dbapi, room_manager_dbapi)
        # print("Данные занесены в базу данных!")

        # # Проверка методов выборки тренеров в определённом зале
        # trainers = trainer_manager_orm.select_trainers_by_room(1)
        # print(*trainers)
        # print()
        # trainers = trainer_manager_dbapi.select_trainers_by_room(1)
        # print(*trainers)

        # # Проверка метода изменения данных о тренере
        # trainer_manager_orm.update_trainer_room(1, 2)
        # trainer_manager_dbapi.update_trainer_room(2, 2)

        # trainers = trainer_manager_dbapi.select_trainers_by_room(1)
        # print(*trainers)
        # print()
        # trainers = trainer_manager_dbapi.select_trainers_by_room(2)
        # print(*trainers)

        # trainer_manager_orm.update_trainer_room(1, 1)
        # trainer_manager_dbapi.update_trainer_room(2, 1)

        # print()
        # # Возвращаем как было
        # trainers = trainer_manager_dbapi.select_trainers_by_room(1)
        # print(*trainers)
        # print()
        # trainers = trainer_manager_dbapi.select_trainers_by_room(2)
        # print(*trainers)

        # Тест метода удаления тренера или зала
        # trainer_manager_orm.delete_trainer(6)
        # trainer_manager_dbapi.add_trainer("Волков Дмитрий Андреевич", "TRX", 4, 2)
        # trainer_manager_dbapi.delete_trainer(6)

        #room_manager_orm.delete_room(4)
        # room_manager_dbapi.add_room("Зал групповых программ", "ул. Космонавтов, 2", 25)
        # room_manager_dbapi.delete_room(4)

        # Тест метода вычисления общего кол-ва оборудования, используемого каждым тренером
        # equipment_data = equipment_manager_dbapi.calculate_all_trainer_equipment()
        # print(equipment_data)
        # equipment_data = equipment_manager_orm.calculate_all_trainer_equipment()
        # print(equipment_data)
    except Exception as e:
        print(e)

    # Задание 2

    # Создаём init миграцию коммандой alembic <Название миграции> <Название директории для миграций>
    # alembic init migrations

    # Необходимо сконфигурировать появившийся файл alembic.ini:

    # 1. Установить 'sqlalchemy.url' на строку подключения к базе данных 
    # ('sqlite:///kachalka.db')
    # env.py -> config.set_main_option('sqlalchemy.url', 'sqlite:///kachalka.db')

    # 2. Импортировать модели
    # env.py ->
    # from main import Base
    # target_metadata = Base.metadata

    # 3. Создаём миграцию alembic revision --autogenerate
    # В дальнейшем, при добавлении новых таблиц, или изменении структуры уже
    # существующих, с помощью миграций заносим изменения в БД

    # alembic upgrade head  - накатить все существующие миграции на БД
    # alembic upgrade <revision> - накатить все существующие миграции до определённой версии на БД
    # alembic downgrade - откатить миграцию


