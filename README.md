
# 📡 master-thesis-rfid-sim

**Имитационная модель RFID системы с подвижной меткой (2022)**

Старая версия модели, разработанная в рамках магистерской диссертации.

## 📌 Описание проекта
Данный проект представляет собой дискретно-событийную **имитационную модель взаимодействия RFID считывателя и меток**, размещённых на поверхности земли. Модель учитывает движение метки и реализацию команд протокола EPC Gen2.

Проект был написан для магистерской диссертации и является **предшественником** более продвинутой модели, разработанной для кандидатской диссертации (см. [новый репозиторий](https://github.com/VilmenAbramian/simulation)). Несмотря на упрощения, текущая реализация успешно моделирует ключевые аспекты RFID протокола и служит хорошей основой для понимания логики инвентаризации и передачи данных в мобильной RFID среде.

## ⚙️ Основной функционал

- Дискретно-событийное моделирование раундов инвентаризации (Query, QueryRep, Ack, Read и т.д.);
- Учёт параметра `Q` и вероятности коллизий;
- Поддержка перемещения метки и динамики зоны видимости;
- Статистика по вероятности чтения;
- Наличие простого CLI интерфейса.

## English version

** RFID System Simulation Model with a Mobile Tag (2022)**

An earlier version of the model developed as part of a master's thesis.

## 📌 Project Overview

This project is a discrete-event **simulation model of interaction between an RFID reader and tags** placed on the ground surface. The model takes into account tag movement and implements key commands from the EPC Gen2 protocol.

The project was developed for a master's thesis and serves as a **predecessor** to a more advanced model created for a PhD dissertation (see [new repository](https://github.com/VilmenAbramian/simulation)). Despite its simplified design, this version successfully captures core aspects of the RFID protocol and provides a solid foundation for understanding inventory logic and data transmission in mobile RFID environments.

## ⚙️ Key Features

- Discrete-event simulation of inventory rounds (Query, QueryRep, Ack, Read, etc.);
- Support for parameter `Q` and collision probability;
- Tag movement and dynamic visibility zone;
- Read success probability statistics;
- Simple CLI interface.
