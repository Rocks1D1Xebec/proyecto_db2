drop database if exists Lyra;
create database Lyra;

use Lyra;

create table usuario (
    id int unsigned primary key auto_increment,
    nombre varchar(50) unique not null,
    correo varchar(100) unique not null,
    contrasena varchar(255) not null,
    fecha_registro datetime not null default current_timestamp
) engine=innodb;

create table artista (
    id int unsigned primary key auto_increment,
    nombre varchar(100) unique not null
) engine=innodb;

create table cancion (
    id int unsigned primary key auto_increment,
    titulo varchar(100),
    id_youtube varchar(50) unique not null,
    id_artista int unsigned not null,
    id_usuario_subio int unsigned not null,
    duracion int unsigned not null,
    link_r2 text not null,
    formato varchar(10) not null default 'mp3',
    fecha_subida datetime not null,
    constraint fk_cancion_artista foreign key (id_artista) references artista(id),
    constraint fk_cancion_usuario foreign key (id_usuario_subio) references usuario(id)
) engine=innodb;

create table lista (
    id int unsigned primary key auto_increment,
    nombre varchar(100) not null,
    id_usuario int unsigned not null,
    constraint uq_usuario_lista unique (id_usuario, nombre),
    constraint fk_lista_usuario foreign key (id_usuario) references usuario(id)
) engine=innodb;

create table detalle_lista (
    id int unsigned primary key auto_increment,
    id_cancion int unsigned not null,
    id_lista int unsigned not null,
    posicion int unsigned not null,
    constraint uq_lista_cancion unique (id_lista, id_cancion),
    constraint fk_detalle_lista_cancion foreign key (id_cancion) references cancion(id),
    constraint fk_detalle_lista_lista foreign key (id_lista) references lista(id)
) engine=innodb;

create table me_gusta (
    id int unsigned primary key auto_increment,
    id_usuario int unsigned not null,
    id_cancion int unsigned not null,
    fecha_agregado datetime not null default current_timestamp,
    constraint uq_usuario_cancion unique (id_usuario, id_cancion),
    constraint fk_me_gusta_usuario foreign key (id_usuario) references usuario(id),
    constraint fk_me_gusta_cancion foreign key (id_cancion) references cancion(id)
) engine=innodb;

insert into usuario (nombre, correo, contrasena) values 
('Cusi Quispe Wilfredo', 'cusiwachero@gmail.com', 'cusi123'),
('Senku Ishigami', 'senku@@gmail.com', 'senku123'),
('Rocks D. Xebec', 'rocksDxebec@gmail.com', 'good_valley'),
('Son Goku', 'goku@gmail.com', 'genkidama'),
('Vegeta', 'vegeta@gmail.com', 'insecto'),
('Sora', 'sora@gmail.com', 'no_game'),
('Shiro', 'shiro@gmail.com', 'no_life'),
('Tanjiro Kamado', 'tanjiro@gmail.com', 'solar'),
('Zenitsu Agatsuma', 'zenitsu@gmail.com', 'amarillo'),
('Gen Asagiri', 'gen@gmail.com', 'mentalista');

insert into artista (nombre) values 
('Hironobu Kageyama'),
('BURNOUT SYNDROMES'),
('LiSA'),
('Konomi Suzuki'),
('Hiroshi Kitadani'),
('Grupo Maroyu'),
('Peluchin y Su Grupo'),
('Aimer'),
('FLOW'),
('Unison Square Garden');

insert into cancion (titulo, id_youtube, id_artista, id_usuario_subio, duracion, link_r2, formato, fecha_subida) values 
('Cha-La Head-Cha-La', 'GHnfX1RmZX8', 1, 4, 198, 'https://r2.lyramusic.app/audio/GHnfX1RmZX8.mp3', 'mp3', '2026-10-15 10:00:00'),
('Good Morning World!', 'b4GzWq_w1x8', 2, 2, 205, 'https://r2.lyramusic.app/audio/b4GzWq_w1x8.mp3', 'mp3', '2026-10-16 11:30:00'),
('Gurenge', 'CwkzK-F0Y00', 3, 8, 236, 'https://r2.lyramusic.app/audio/CwkzK-F0Y00.mp3', 'mp3', '2026-10-17 12:45:00'),
('This Game', 'j6Tj5q_Q4g0', 4, 6, 284, 'https://r2.lyramusic.app/audio/j6Tj5q_Q4g0.mp3', 'mp3', '2026-10-18 15:20:00'),
('We Are!', 'Zw_x2J4a8x9', 5, 3, 240, 'https://r2.lyramusic.app/audio/Zw_x2J4a8x9.mp3', 'mp3', '2026-10-19 16:10:00'),
('Lunita Dame Platita', 'cusi_mry_001', 6, 1, 215, 'https://r2.lyramusic.app/audio/cusi_mry_001.mp3', 'mp3', '2026-10-20 09:00:00'),
('El Baile del Wachero', 'cusi_wch_002', 7, 1, 190, 'https://r2.lyramusic.app/audio/cusi_wch_002.mp3', 'mp3', '2026-10-21 14:00:00'),
('Zankyosanka', 'tLQLa6lM3Us', 8, 9, 184, 'https://r2.lyramusic.app/audio/tLQLa6lM3Us.mp3', 'mp3', '2026-10-22 17:15:00'),
('Sign', 'qpx7yG8b71k', 9, 5, 235, 'https://r2.lyramusic.app/audio/qpx7yG8b71k.mp3', 'mp3', '2026-10-23 18:30:00'),
('Sugar Song to Bitter Step', '3exsRhw3xt8', 10, 10, 254, 'https://r2.lyramusic.app/audio/3exsRhw3xt8.mp3', 'mp3', '2026-10-24 20:00:00');

insert into lista (nombre, id_usuario) values
('Cumbias del Recuerdo', 1),
('Para Programar en la Madrugada', 1),
('10 Billones por Ciento Ritmo', 2),
('Química y Electrónica Experimental', 2),
('Dominio Mundial', 3),
('Batallas de God Valley', 3),
('Entrenamiento en la Habitación del Tiempo', 4),
('Música para Comer 50 Platos', 4),
('Orgullo Saiyajin', 5),
('Superando los Límites de Kakaroto', 5),
('Los Blancos Nunca Pierden', 6),
('Estrategias Imbatibles de Juego', 6),
('Cálculo Perfecto', 7),
('Lo-Fi para Partidas de Ajedrez', 7),
('Danza del Dios del Fuego', 8),
('Protegiendo a Nezuko', 8),
('Pánico y Primera Postura', 9),
('Canciones para Conquistar a Nezuko', 9),
('Psicología y Manipulación Fina', 10),
('Bebiendo Cola Casera con Senku', 10);

insert into detalle_lista (id_lista, id_cancion, posicion) values
(1, 6, 1), (1, 7, 2), (2, 4, 1), (2, 10, 2), (3, 2, 1), (4, 2, 1), (4, 4, 2), (5, 5, 1), (7, 1, 1), 
(7, 9, 2), (9, 1, 1), (9, 9, 2), (11, 4, 1), (13, 4, 1), (15, 3, 1), (15, 8, 2), (17, 8, 1),
(18, 3, 1), (18, 8, 2), (19, 10, 1), (19, 2, 2);

insert into me_gusta (id_usuario, id_cancion, fecha_agregado) values
(1, 6, '2026-10-25 10:00:00'), (1, 7, '2026-10-25 10:05:00'), (1, 1, '2026-10-25 10:10:00'),
(2, 2, '2026-10-25 11:00:00'), (2, 4, '2026-10-25 11:15:00'), (3, 5, '2026-10-25 12:00:00'),
(4, 1, '2026-10-25 13:00:00'), (4, 9, '2026-10-25 13:30:00'), (5, 9, '2026-10-25 14:00:00'),
(5, 1, '2026-10-25 14:15:00'), (6, 4, '2026-10-25 15:00:00'), (6, 10, '2026-10-25 15:10:00'),
(7, 4, '2026-10-25 16:00:00'), (7, 2, '2026-10-25 16:30:00'), (8, 3, '2026-10-25 17:00:00'),
(8, 8, '2026-10-25 17:20:00'), (9, 3, '2026-10-25 18:00:00'), (9, 8, '2026-10-25 18:15:00'),
(10, 10, '2026-10-25 19:00:00'), (10, 2, '2026-10-25 19:25:00');