-- usuario de acceso
create user if not exists 'nyls'@'%' identified by 'nyls123';
grant all privileges on lyra.* to 'nyls'@'%';
flush privileges;

-- creacion de base de datos y tablas
drop database if exists lyra;
create database lyra 
character set utf8mb4 
collate utf8mb4_unicode_ci;

use lyra;

create table usuario (
  id int unsigned primary key auto_increment,
  nombre varchar(50) unique not null,
  correo varchar(100) unique not null,
  contraseña varchar(255) not null,
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

create table bitacora_canciones (
  id int unsigned auto_increment primary key,
  accion varchar(20) not null,
  id_cancion int unsigned,
  titulo varchar(100),
  usuario_subio int unsigned,
  fecha datetime default current_timestamp
) engine=innodb;

-- trigger de auditoria
delimiter $$
create trigger trg_auditoria_subida_cancion
after insert on cancion
for each row
begin
  insert into bitacora_canciones (accion, id_cancion, titulo, usuario_subio)
  values ('subida', new.id, new.titulo, new.id_usuario_subio);
end$$
delimiter ;

-- vistas
create or replace view vw_catalogo_canciones as 
select 
  c.id as id_cancion,
  c.titulo, 
  a.nombre as artista,
  c.duracion, 
  c.link_r2, 
  c.id_youtube, 
  c.fecha_subida, 
  u.nombre as subido_por 
from cancion c
inner join artista a on c.id_artista = a.id
inner join usuario u on c.id_usuario_subio = u.id;

create or replace view vw_canciones_populares as 
select 
  c.id as id_cancion, 
  c.titulo, 
  a.nombre as artista,
  c.duracion,
  c.id_youtube,
  c.link_r2,
  count(m.id) as total_me_gusta 
from cancion c
inner join artista a on c.id_artista = a.id
left join me_gusta m on c.id = m.id_cancion
group by c.id, c.titulo, a.nombre, c.duracion, c.id_youtube, c.link_r2
order by total_me_gusta desc;

-- indices
create index idx_cancion_titulo on cancion(titulo);
create index idx_artista_nombre on artista(nombre);
create index idx_cancion_fecha on cancion(fecha_subida desc);

-- procedimientos almacenados
delimiter $$
drop procedure if exists sp_subir_cancion$$
create procedure sp_subir_cancion(
  in p_titulo varchar(100),
  in p_id_youtube varchar(50),
  in p_nombre_artista varchar(100),
  in p_id_usuario int unsigned,
  in p_duracion int unsigned,
  in p_link_r2 text
)
begin
  declare v_id_artista int unsigned;
  select id into v_id_artista from artista where nombre = p_nombre_artista limit 1;
  if v_id_artista is null then
    insert into artista (nombre) values (p_nombre_artista);
    set v_id_artista = last_insert_id();
  end if;
  insert into cancion (titulo, id_youtube, id_artista, id_usuario_subio, duracion, link_r2, fecha_subida)
  values (p_titulo, p_id_youtube, v_id_artista, p_id_usuario, p_duracion, p_link_r2, now());
end$$
delimiter ;

delimiter $$
drop procedure if exists sp_crear_lista$$
create procedure sp_crear_lista(
  in p_id_usuario int unsigned,
  in p_nombre varchar(100)
)
begin
  insert into lista (nombre, id_usuario) values (p_nombre, p_id_usuario);
  select last_insert_id() as id;
end$$
delimiter ;

delimiter $$
drop procedure if exists sp_eliminar_lista$$
create procedure sp_eliminar_lista(
  in p_id_lista int unsigned,
  in p_id_usuario int unsigned
)
begin
  if exists (select 1 from lista where id = p_id_lista and id_usuario = p_id_usuario) then
    delete from detalle_lista where id_lista = p_id_lista;
    delete from lista where id = p_id_lista and id_usuario = p_id_usuario;
  end if;
end$$
delimiter ;

delimiter $$
drop procedure if exists sp_agregar_cancion_lista$$
create procedure sp_agregar_cancion_lista(
  in p_id_lista int,
  in p_id_cancion int
)
begin
  if not exists (select 1 from detalle_lista where id_lista = p_id_lista and id_cancion = p_id_cancion) then
    insert into detalle_lista (id_lista, id_cancion)
    values (p_id_lista, p_id_cancion);
  end if;
end$$
delimiter ;

delimiter $$
drop procedure if exists sp_eliminar_cancion_lista$$
create procedure sp_eliminar_cancion_lista(
  in p_id_lista int,
  in p_id_cancion int
)
begin
  delete from detalle_lista 
  where id_lista = p_id_lista and id_cancion = p_id_cancion;
end$$
delimiter ;

-- datos de prueba
insert into usuario (nombre, correo, contraseña) values 
('Cusi Quispe Wilfredo', 'cusiwachero@gmail.com', 'cusi123'),
('Senku Ishigami', 'senku@gmail.com', 'senku123'),
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

insert into detalle_lista (id_lista, id_cancion) values
(1, 6), (1, 7), (2, 4), (2, 10), (3, 2), (4, 2), (4, 4), (5, 5), (7, 1), 
(7, 9), (9, 1), (9, 9), (11, 4), (13, 4), (15, 3), (15, 8), (17, 8),
(18, 3), (18, 8), (19, 10), (19, 2);

insert into me_gusta (id_usuario, id_cancion, fecha_agregado) values
(1, 6, '2026-10-25 10:00:00'), (1, 7, '2026-10-25 10:05:00'), (1, 1, '2026-10-25 10:10:00'),
(2, 2, '2026-10-25 11:00:00'), (2, 4, '2026-10-25 11:15:00'), (3, 5, '2026-10-25 12:00:00'),
(4, 1, '2026-10-25 13:00:00'), (4, 9, '2026-10-25 13:30:00'), (5, 9, '2026-10-25 14:00:00'),
(5, 1, '2026-10-25 14:15:00'), (6, 4, '2026-10-25 15:00:00'), (6, 10, '2026-10-25 15:10:00'),
(7, 4, '2026-10-25 16:00:00'), (7, 2, '2026-10-25 16:30:00'), (8, 3, '2026-10-25 17:00:00'),
(8, 8, '2026-10-25 17:20:00'), (9, 3, '2026-10-25 18:00:00'), (9, 8, '2026-10-25 18:15:00'),
(10, 10, '2026-10-25 19:00:00'), (10, 2, '2026-10-25 19:25:00');
