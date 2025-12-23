CREATE TABLE athletes (
    athlete_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL
);

CREATE TABLE workout_sessions (
    session_id INT IDENTITY(1,1) PRIMARY KEY,
    athlete_id INT NOT NULL,
    session_date DATE NOT NULL,
    source_file NVARCHAR(255),
    notes NVARCHAR(MAX),
    CONSTRAINT FK_sessions_athletes FOREIGN KEY (athlete_id)
        REFERENCES athletes(athlete_id)
);

CREATE TABLE exercises (
    exercise_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    category NVARCHAR(50),
    body_region NVARCHAR(50),
    is_compound BIT
);

CREATE TABLE sets (
    set_id INT IDENTITY(1,1) PRIMARY KEY,
    session_id INT NOT NULL,
    exercise_id INT NOT NULL,
    set_number INT NOT NULL,
    reps INT NOT NULL,
    weight FLOAT,
    rpe FLOAT,
    notes NVARCHAR(MAX),
    CONSTRAINT FK_sets_sessions FOREIGN KEY (session_id)
        REFERENCES workout_sessions(session_id),
    CONSTRAINT FK_sets_exercises FOREIGN KEY (exercise_id)
        REFERENCES exercises(exercise_id)
);

INSERT INTO athletes (name) VALUES ('Alex Lim');
SELECT * FROM athletes;