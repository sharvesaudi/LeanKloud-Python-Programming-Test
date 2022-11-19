CREATE TABLE `tasks` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task` varchar(2000) NOT NULL,
  `due_date` date DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'Not Started',
  PRIMARY KEY (`id`)
) ;

INSERT INTO `tasks` VALUES (1,'Learn Flask','2022-11-18','Finished'),
(2,'Add Database','2022-11-19','Finished'),
(3,'Submission','2022-11-19','Not Started'),
(4,'Adding resume','2022-11-22','In Progress'),
(5,'Screencast','2022-11-20','Not Started');

CREATE TABLE `user` (
  `username` varchar(200) NOT NULL,
  `password` varchar(200) NOT NULL,
  `role` varchar(20) DEFAULT 'read',
  PRIMARY KEY (`username`)
);

INSERT INTO `user` VALUES ('sharves','password','read'),('admin','password','write');

select * from user;
