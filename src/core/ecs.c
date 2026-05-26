/**
 * @file ecs.c
 * @brief Реализация ECS на разреженных множествах.
 */

#include "ecs.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "memory.h"

ecs_world_t* ecs_world_create(void) {
	ecs_world_t* world = mem_alloc(sizeof(ecs_world_t));

	if (world == NULL) {
		return NULL;
	}

	memset(world, 0, sizeof(ecs_world_t));

	return world;
}

void ecs_world_destroy(ecs_world_t* world) {
	if (world == NULL) {
		return;
	}

	for (ecs_component_type_t i = 0; i < ECS_MAX_COMPONENT_TYPES; i++) {
		mem_free(world->pools[i].components);
		world->pools[i].components = NULL;
	}

	mem_free(world);
}

ecs_entity_t ecs_entity_create(ecs_world_t* world) {
	if (world == NULL) {
		return 0;
	}

	for (ecs_entity_t i = 1; i < ECS_MAX_ENTITIES; i++) { /* 0 зарезервирован как "нет сущности" */
		if (!world->entity_alive[i]) {
			world->entity_alive[i] = true;
			world->entity_mask[i] = 0;
			return i;
		}
	}

	return 0;
}

void ecs_entity_destroy(ecs_world_t* world, ecs_entity_t entity) {
	if (world == NULL || entity == 0 || entity >= ECS_MAX_ENTITIES) {
		return;
	}

	/* Удаляем все компоненты */
	uint64_t mask = world->entity_mask[entity];

	for (ecs_component_type_t t = 0; t < ECS_MAX_COMPONENT_TYPES; t++) {
		if (mask & (1ULL << t)) {
			ecs_component_remove(world, entity, t);
		}
	}

	world->entity_alive[entity] = false;
}

ecs_component_type_t ecs_component_register(ecs_world_t* world, size_t comp_size) {
	if (world == NULL || comp_size == 0) {
		return ECS_MAX_COMPONENT_TYPES;
	}

	for (ecs_component_type_t i = 0; i < ECS_MAX_COMPONENT_TYPES; i++) {
		if (world->pools[i].component_size == 0) {
			world->pools[i].component_size = comp_size;
			return i;
		}
	}

	return ECS_MAX_COMPONENT_TYPES;
}

void* ecs_component_add(ecs_world_t* world, ecs_entity_t entity, ecs_component_type_t type) {
	if (world == NULL || entity == 0 || entity >= ECS_MAX_ENTITIES || type >= ECS_MAX_COMPONENT_TYPES) {
		return NULL;
	}

	if (world->pools[type].component_size == 0) {
		return NULL; /* Тип не зарегистрирован */
	}

	ecs_component_pool_t* pool = &world->pools[type];

	/* Ленивое выделение памяти под массив компонентов */
	if (pool->components == NULL) {
		pool->components = mem_alloc(ECS_MAX_ENTITIES * pool->component_size);

		if (pool->components == NULL) {
			return NULL;
		}

		memset(pool->components, 0, ECS_MAX_ENTITIES * pool->component_size);
	}

	pool->presence[entity] = true;
	world->entity_mask[entity] |= (1ULL << type);

	return (uint8_t*)pool->components + (entity * pool->component_size);
}

void* ecs_component_get(const ecs_world_t* world, ecs_entity_t entity, ecs_component_type_t type) {
	if (world == NULL || entity == 0 || entity >= ECS_MAX_ENTITIES || type >= ECS_MAX_COMPONENT_TYPES) {
		return NULL;
	}

	const ecs_component_pool_t* pool = &world->pools[type];

	if (!pool->presence[entity]) {
		return NULL;
	}

	return (uint8_t*)pool->components + (entity * pool->component_size);
}

void ecs_component_remove(ecs_world_t* world, ecs_entity_t entity, ecs_component_type_t type) {
	if (world == NULL || entity == 0 || entity >= ECS_MAX_ENTITIES || type >= ECS_MAX_COMPONENT_TYPES) {
		return;
	}

	ecs_component_pool_t* pool = &world->pools[type];
	pool->presence[entity] = false;
	world->entity_mask[entity] &= ~(1ULL << type);
}