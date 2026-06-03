/**
 * @file entity_manager.c
 * @brief Реализация пулов сущностей и компонентов (без динамической памяти).
 */

#include "entity_manager.h"

#include <string.h>

// Битовый массив существования сущностей (1 – используется, 0 – свободен)
static uint8_t entities_used[(MAX_ENTITIES + 7) / 8];

// Пулы компонентов (фиксированные массивы, индексируемые ID сущности)
static Position positions[MAX_ENTITIES];
static uint8_t has_position[MAX_ENTITIES];	// флаг наличия компонента

static Velocity velocities[MAX_ENTITIES];
static uint8_t has_velocity[MAX_ENTITIES];

static Sprite sprites[MAX_ENTITIES];
static uint8_t has_sprite[MAX_ENTITIES];

// Вспомогательные макросы для битового массива
#define BIT_INDEX(e) ((e) >> 3)
#define BIT_MASK(e) (1u << ((e) & 7))

static int is_entity_used(uint32_t entity) {
	return (entities_used[BIT_INDEX(entity)] & BIT_MASK(entity)) != 0;
}

static void set_entity_used(uint32_t entity, int used) {
	if (used) {
		entities_used[BIT_INDEX(entity)] |= BIT_MASK(entity);
	} else {
		entities_used[BIT_INDEX(entity)] &= ~BIT_MASK(entity);
	}
}

void entity_manager_init(void) {
	memset(entities_used, 0, sizeof(entities_used));
	memset(has_position, 0, sizeof(has_position));
	memset(has_velocity, 0, sizeof(has_velocity));
	memset(has_sprite, 0, sizeof(has_sprite));
	// Массивы positions, velocities, sprites обнулять необязательно, но безопаснее:
	memset(positions, 0, sizeof(positions));
	memset(velocities, 0, sizeof(velocities));
	memset(sprites, 0, sizeof(sprites));
}

uint32_t create_entity(void) {
	// Ищем первый свободный слот (начиная с 1, т.к. 0 резервируем как "не сущность")
	for (uint32_t i = 1; i < MAX_ENTITIES; ++i) {
		if (!is_entity_used(i)) {
			set_entity_used(i, 1);
			return i;
		}
	}
	return 0;  // нет свободных слотов
}

void destroy_entity(uint32_t entity) {
	if (entity == 0 || entity >= MAX_ENTITIES) {
		return;
	}

	if (!is_entity_used(entity)) {
		return;
	}

	// Удаляем все компоненты
	has_position[entity] = 0;
	has_velocity[entity] = 0;
	has_sprite[entity] = 0;

	// Освобождаем слот сущности
	set_entity_used(entity, 0);
}

// --- Position ---

int has_position(uint32_t entity) {
	if (entity == 0 || entity >= MAX_ENTITIES) {
		return 0;
	}

	return has_position[entity];
}

void add_position(uint32_t entity, float x, float y) {
	if (entity == 0 || entity >= MAX_ENTITIES) {
		return;
	}

	if (!is_entity_used(entity)) {
		return;
	}

	positions[entity].x = x;
	positions[entity].y = y;
	has_position[entity] = 1;
}

Position* get_position(uint32_t entity) {
	if (entity == 0 || entity >= MAX_ENTITIES) {
		return NULL;
	}

	if (!has_position[entity]) {
		return NULL;
	}

	return &positions[entity];
}

// --- Velocity ---

int has_velocity(uint32_t entity) {
	if (entity == 0 || entity >= MAX_ENTITIES) {
		return 0;
	}

	return has_velocity[entity];
}

void add_velocity(uint32_t entity, float vx, float vy) {
	if (entity == 0 || entity >= MAX_ENTITIES) {
		return;
	}

	if (!is_entity_used(entity)) {
		return;
	}

	velocities[entity].vx = vx;
	velocities[entity].vy = vy;
	has_velocity[entity] = 1;
}

Velocity* get_velocity(uint32_t entity) {
	if (entity == 0 || entity >= MAX_ENTITIES) {
		return NULL;
	}

	if (!has_velocity[entity]) {
		return NULL;
	}

	return &velocities[entity];
}

// --- Sprite ---

int has_sprite(uint32_t entity) {
	if (entity == 0 || entity >= MAX_ENTITIES) {
		return 0;
	}

	return has_sprite[entity];
}

void add_sprite(uint32_t entity, uint8_t r, uint8_t g, uint8_t b, int w, int h) {
	if (entity == 0 || entity >= MAX_ENTITIES) {
		return;
	}

	if (!is_entity_used(entity)) {
		return;
	}

	sprites[entity].r = r;
	sprites[entity].g = g;
	sprites[entity].b = b;
	sprites[entity].w = w;
	sprites[entity].h = h;
	has_sprite[entity] = 1;
}

Sprite* get_sprite(uint32_t entity) {
	if (entity == 0 || entity >= MAX_ENTITIES) {
		return NULL;
	}

	if (!has_sprite[entity]) {
		return NULL;
	}
    
	return &sprites[entity];
}