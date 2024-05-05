
CREATE TABLE Admin (
    AdminId SERIAL PRIMARY KEY,
    Name VARCHAR(50) NOT NULL,
    Password VARCHAR(50) NOT NULL
);

INSERT INTO Admin (Name, Password) VALUES ('ahmed', '123');
INSERT INTO Admin (Name, Password) VALUES ('mohamed', '123');
INSERT INTO Admin (Name, Password) VALUES ('waleed', '123');

CREATE TABLE Image (
    ImageId SERIAL PRIMARY KEY,
    AdminId INTEGER REFERENCES Admin(AdminId),
    TimeStamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    Source VARCHAR(50),
    ImagePath VARCHAR(255)
);

CREATE TABLE Face (
    FaceID SERIAL PRIMARY KEY,
    ImageId INTEGER REFERENCES Image(ImageId),
    BoundryBox VARCHAR(50)
);

CREATE TABLE GenderPrediction (
    PredictionID SERIAL PRIMARY KEY,
    FaceID INTEGER REFERENCES Face(FaceID),
    GenderPredicted VARCHAR(10) NOT NULL,
    Confidence REAL NOT NULL
);

CREATE TABLE AgePrediction (
    PredictionID SERIAL PRIMARY KEY,
    FaceID INTEGER REFERENCES Face(FaceID),
    AgePredicted VARCHAR(10) NOT NULL,
    Confidence REAL NOT NULL
);

CREATE OR REPLACE FUNCTION InsertData(
    AdminName VARCHAR(50),
    Source VARCHAR(50),
    ImagePath VARCHAR(255),
    BoundryBox VARCHAR(50),
    GenderPredicted VARCHAR(10),
    GenderConfidence REAL,
    AgePredicted VARCHAR(10),
    AgeConfidence REAL
)
RETURNS VOID
AS $$
DECLARE
    AdminIdVar INTEGER;
    ImageIdVar INTEGER;
    FaceIdVar INTEGER;
BEGIN
    SELECT AdminId INTO AdminIdVar FROM Admin WHERE Name = AdminName;

    IF FOUND THEN

        SELECT ImageId INTO ImageIdVar FROM Image WHERE Image.ImagePath = InsertData.ImagePath LIMIT 1;

        IF NOT FOUND THEN
            INSERT INTO Image (AdminId, Source, ImagePath)
            VALUES (AdminIdVar, Source, ImagePath)
            RETURNING ImageId INTO ImageIdVar;
        END IF;

        INSERT INTO Face (ImageId, BoundryBox)
        VALUES (ImageIdVar, BoundryBox)
        RETURNING FaceID INTO FaceIdVar;

        INSERT INTO GenderPrediction (FaceID, GenderPredicted, Confidence)
        VALUES (FaceIdVar, GenderPredicted, GenderConfidence);

        INSERT INTO AgePrediction (FaceID, AgePredicted, Confidence)
        VALUES (FaceIdVar, AgePredicted, AgeConfidence);
    ELSE
        RAISE NOTICE 'Admin does not exist';
    END IF;
END;
$$ LANGUAGE plpgsql;
