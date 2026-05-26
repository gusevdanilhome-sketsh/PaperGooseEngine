/**
 * @file movement.c
 * @brief Система перемещения сущностей.
 */

#include <stddef.h>

#include "../core/ecs.h"

/* Компоненты, ожидаемые системой, должны быть зарегистрированы снаружи. */
/* Идентификаторы типов компонентов передаются через глобальные переменные или контекст. */
/* Здесь для наглядности используем прямые идентификаторы из main.c */

/**
 * @brief Обновить позиции сущностей с компонентами Position и Velocity.
 * @param[in] world Указатель на мир ECS.
 * @param[in] pos_type Идентификатор компонента Position.
 * @param[in] vel_type Идентификатор компонента Velocity.
 * @param[in] dt Дельта времени (сек).
 */
void movement_system(ecs_world_t* world, ecs_component_type_t pos_type, ecs_component_type_t vel_type, float dt) {
	if (world == NULL || dt <= 0.0f) {
		return;
	}

	for (ecs_entity_t e = 1; e < ECS_MAX_ENTITIES; e++) {
		if (!world->entity_alive[e]) {
			continue;
		}

		uint64_t mask = world->entity_mask[e];
		uint64_t required = (1ULL << pos_type) | (1ULL << vel_type);
        
		if ((mask & required) != required) {
			continue;
		}

		float* pos_x = (float*)ecs_component_get(world, e, pos_type);
		float* pos_y = pos_x + 1; /* предполагаем, что Position = { float x, y; } */
		float* vel_vx = (float*)ecs_component_get(world, e, vel_type);
		float* vel_vy = vel_vx + 1; /* Velocity = { float vx, vy; } */

		*pos_x += *vel_vx * dt;
		*pos_y += *vel_vy * dt;
	}
}