-- Создание таблицы приоритетов
CREATE TABLE public.priorities (
    id SERIAL PRIMARY KEY,
    priorityname CHARACTER VARYING(50) NOT NULL
);

-- Создание таблицы статусов
CREATE TABLE public.statuses (
    id SERIAL PRIMARY KEY,
    statusname CHARACTER VARYING(50) NOT NULL
);

-- Создание таблицы пользователей
CREATE TABLE public.users (
    id SERIAL PRIMARY KEY,
    telegramid CHARACTER VARYING(10),
    notifications_enabled BOOLEAN DEFAULT TRUE
);

-- Создание таблицы задач с явными внешними ключами
CREATE TABLE public.tasks (
    id SERIAL PRIMARY KEY,
    statusid INTEGER NOT NULL,
    priorityid INTEGER NOT NULL,
    title CHARACTER VARYING(200) NOT NULL,
    description TEXT,
    createdat TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updatedat TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    duedate TIMESTAMP WITHOUT TIME ZONE,
    CONSTRAINT fk_status FOREIGN KEY (statusid) REFERENCES public.statuses(id),
    CONSTRAINT fk_priority FOREIGN KEY (priorityid) REFERENCES public.priorities(id)
);

-- Создание таблицы назначений задач с явными внешними ключами
CREATE TABLE public.tasksasignments (
    id SERIAL PRIMARY KEY,
    taskid INTEGER NOT NULL,
    userid INTEGER NOT NULL,
    assigndate TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    CONSTRAINT fk_task FOREIGN KEY (taskid) REFERENCES public.tasks(id) ON DELETE CASCADE,
    CONSTRAINT fk_user FOREIGN KEY (userid) REFERENCES public.users(id) ON DELETE CASCADE
);

-- Вставка начальных данных для статусов
INSERT INTO public.statuses (statusname) VALUES
('В работе'),
('Завершена'),
('Просрочена');

-- Вставка начальных данных для приоритетов
INSERT INTO public.priorities (priorityname) VALUES
('Низкий'),
('Средний'),
('Высокий');