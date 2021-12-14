INSERT INTO	Formula 
	(MPNum,Version,FormName)
VALUES
	(2112,2.0,'PURPLE PRINT');

----------------------------------

INSERT INTO Component 
	(IntCode,IntDesc)
VALUES
	('N202SP','WHITE'),
	('N911SP','VIOLET'),
	('N913SP','MAGENTA');

--------------------------------------

INSERT INTO Makeup
	(FormNum,FormVersion,CompCode,GramsPerPint)
VALUES
	(2112, 2.0,'N202SP',272.5),
	(2112, 2.0,'N911SP',216.2),
	(2112, 2.0,'N913SP',35.6),
	(2112, 2.0,'N923SP',5.3);

-----------------------------------

UPDATE Formula
SET Notes = 'This is a test note'
WHERE MPNum = 2112 AND Version = 2.0;