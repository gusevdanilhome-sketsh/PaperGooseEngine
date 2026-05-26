/**
 * @file main.c
 * @brief Главный цикл игры. Демонстрация Фазы 0.
 *
 * Компоненты:
 * - Position: { float x, y; }
 * - Velocity: { float vx, vy; }
 * - Sprite:   { int texture_id; }
 */

#include <stdio.h>

#include "core/ecs.h"
#include "core/memory.h"
#include "core/resource.h"
#include "platform/window.h"

/* Глобальные константы */
enum {
	WINDOW_WIDTH = 800,
	WINDOW_HEIGHT = 600,
};

/* Прототипы систем */
extern void movement_system(ecs_world_t* world, ecs_component_type_t pos_type, ecs_component_type_t vel_type, float dt);
extern void render_system(const ecs_world_t* world, ecs_component_type_t pos_type, ecs_component_type_t spr_type,
						  SDL_Renderer* renderer, const resource_manager_t* tex_manager);

int main(int argc, char* argv[]) {
    (void)argc;
    (void)argv;
	
	window_t* win = window_create("Atomy Engine - Phase 0", WINDOW_WIDTH, WINDOW_HEIGHT);
    
	if (win == NULL) {
		return EXIT_FAILURE;
	}

	ecs_world_t* world = ecs_world_create();

	if (world == NULL) {
		window_destroy(win);
		return EXIT_FAILURE;
	}

	resource_manager_t* res_mgr = resource_manager_create(win->sdl_renderer);

	if (res_mgr == NULL) {
		ecs_world_destroy(world);
		window_destroy(win);
		return EXIT_FAILURE;
	}

	/* Регистрация компонентов */
	ecs_component_type_t pos_type = ecs_component_register(world, 2 * sizeof(float)); /* Position: x, y */
	ecs_component_type_t vel_type = ecs_component_register(world, 2 * sizeof(float)); /* Velocity: vx, vy */
	ecs_component_type_t spr_type = ecs_component_register(world, sizeof(int));		  /* Sprite: texture_id */

	/* Загрузка текстуры (заглушка, должен существовать assets/textures/player.png) */
	int player_tex = resource_texture_load(res_mgr, "assets/textures/player.png");
	if (player_tex == 0) {
		fprintf(stderr, "WARNING: player texture not found, using white square\n");
		/* Можно продолжить без текстуры */
	}

	/* Создание тестовой сущности */
	ecs_entity_t player = ecs_entity_create(world);
	{
		float* pos = (float*)ecs_component_add(world, player, pos_type);

		if (pos != NULL) {
			pos[0] = 100.0f; /* x */
			pos[1] = 100.0f; /* y */
		}
		float* vel = (float*)ecs_component_add(world, player, vel_type);

		if (vel != NULL) {
			vel[0] = 50.0f; /* vx пикселей/сек */
			vel[1] = 30.0f; /* vy */
		}
		int* spr = (int*)ecs_component_add(world, player, spr_type);

		if (spr != NULL) {
			*spr = player_tex;
		}
	}

	/* Главный цикл */
	uint64_t last_ticks = SDL_GetPerformanceCounter();
	const uint64_t freq = SDL_GetPerformanceFrequency();

	while (!win->should_close) {
		window_poll_events(win);

		uint64_t now_ticks = SDL_GetPerformanceCounter();
		float dt = (float)(now_ticks - last_ticks) / freq;
		last_ticks = now_ticks;

		/* Ограничение dt, чтобы избежать гигантских скачков при отладке */
		if (dt > 0.05f) {
			dt = 0.05f;
		}

		movement_system(world, pos_type, vel_type, dt);

		window_clear(win, 30, 30, 30);
		render_system(world, pos_type, spr_type, win->sdl_renderer, res_mgr);
		window_present(win);

		SDL_Delay(1); /* Небольшая задержка для снижения нагрузки CPU */
	}

	/* Очистка */
	ecs_entity_destroy(world, player);
	resource_manager_destroy(res_mgr);
	ecs_world_destroy(world);
	window_destroy(win);

	return EXIT_SUCCESS;
}