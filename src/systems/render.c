/**
 * @file render.c
 * @brief Система рендеринга спрайтов.
 */

#include <SDL.h>

#include "../core/ecs.h"
#include "../core/resource.h"

/**
 * @brief Отрисовать все сущности с компонентами Position и Sprite.
 * @param[in] world Указатель на мир ECS.
 * @param[in] pos_type Идентификатор компонента Position.
 * @param[in] spr_type Идентификатор компонента Sprite.
 * @param[in] renderer SDL_Renderer.
 * @param[in] tex_manager Менеджер текстур.
 */
void render_system(const ecs_world_t* world, ecs_component_type_t pos_type, ecs_component_type_t spr_type,
				   SDL_Renderer* renderer, const resource_manager_t* tex_manager) {
	if (world == NULL || renderer == NULL || tex_manager == NULL) {
		return;
	}

	for (ecs_entity_t e = 1; e < ECS_MAX_ENTITIES; e++) {
		if (!world->entity_alive[e]) {
			continue;
		}

		uint64_t mask = world->entity_mask[e];
		uint64_t required = (1ULL << pos_type) | (1ULL << spr_type);

		if ((mask & required) != required) {
			continue;
		}

		float* pos_x = (float*)ecs_component_get(world, e, pos_type);
		float* pos_y = pos_x + 1;
		int* tex_id = (int*)ecs_component_get(world, e, spr_type);

		SDL_Texture* tex = resource_texture_get(tex_manager, *tex_id);

		if (tex == NULL) {
			continue;
		}

		SDL_Rect dst = {(int)(*pos_x), (int)(*pos_y), 32, 32}; /* Размер спрайта фиксирован 32x32 */
		SDL_RenderCopy(renderer, tex, NULL, &dst);
	}
}