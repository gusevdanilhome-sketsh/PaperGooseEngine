/**
 * @file window.c
 * @brief Реализация оконной обёртки.
 */

#include "window.h"

#include <stdio.h>

#include "../core/memory.h"

window_t* window_create(const char* title, int width, int height) {
	if (SDL_Init(SDL_INIT_VIDEO) != 0) {
		fprintf(stderr, "ERROR: SDL_Init failed: %s\n", SDL_GetError());
		return NULL;
	}

	window_t* win = mem_alloc(sizeof(window_t));

	if (win == NULL) {
		SDL_Quit();
		return NULL;
	}

	win->width = width;
	win->height = height;
	win->should_close = false;

	win->sdl_window =
		SDL_CreateWindow(title, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED, width, height, SDL_WINDOW_SHOWN);

	if (win->sdl_window == NULL) {
		fprintf(stderr, "ERROR: SDL_CreateWindow failed: %s\n", SDL_GetError());
		mem_free(win);
		SDL_Quit();
		return NULL;
	}

	win->sdl_renderer = SDL_CreateRenderer(win->sdl_window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);

	if (win->sdl_renderer == NULL) {
		fprintf(stderr, "ERROR: SDL_CreateRenderer failed: %s\n", SDL_GetError());
		SDL_DestroyWindow(win->sdl_window);
		mem_free(win);
		SDL_Quit();
		return NULL;
	}

	return win;
}

void window_destroy(window_t* win) {
	if (win == NULL) {
		return;
	}

	SDL_DestroyRenderer(win->sdl_renderer);
	SDL_DestroyWindow(win->sdl_window);
	mem_free(win);
	SDL_Quit();
}

void window_poll_events(window_t* win) {
	if (win == NULL) {
		return;
	}

	SDL_Event event;

	while (SDL_PollEvent(&event)) {
		if (event.type == SDL_QUIT) {
			win->should_close = true;
		} else if (event.type == SDL_KEYDOWN && event.key.keysym.sym == SDLK_ESCAPE) {
			win->should_close = true;
		}
	}
}

void window_clear(const window_t* win, uint8_t r, uint8_t g, uint8_t b) {
	if (win == NULL || win->sdl_renderer == NULL) {
		return;
	}

	SDL_SetRenderDrawColor(win->sdl_renderer, r, g, b, 255);
	SDL_RenderClear(win->sdl_renderer);
}

void window_present(window_t* win) {
	if (win == NULL || win->sdl_renderer == NULL) {
		return;
	}

	SDL_RenderPresent(win->sdl_renderer);
}