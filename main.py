import sqlite3

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from abc import ABC, abstractmethod

# ORM настройка
# В будущем переделать под PostgreSQL или MSSql
engine = create_engine('sqlite:///kachalka.db')

Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

# Подключение к базе данных
conn = sqlite3.connect('kachalka.db')
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

# Модель для сущности "Спортивное оборудование"
class Equipment(Base):
    __tablename__ = 'equipment'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)

# Модель для сущности "Оборудование закреплённое за тренером"
class TrainerEquipment(Base):
    # Составной первичный ключ для обеспечения уникальности пар значений 
    # trainer-equipment
    __tablename__ = 'trainer_equipment'
    trainer_id = Column(Integer, ForeignKey('trainers.id'), primary_key=True)
    equipment_id = Column(Integer, ForeignKey('equipment.id'), primary_key=True)
    quantity = Column(Integer, nullable=False)

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


if __name__ == '__main__':
    pass
    # Создание базы данных и таблиц, если они не существуют.
    # Для первоначальной настройки. Alembic обрабатывает последующие изменения.
    # Base.metadata.create_all(engine) # запустить один раз


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


