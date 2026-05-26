/**
 * @file resource.c
 * @brief Реализация менеджера текстур.
 */

#include "resource.h"

#include <SDL_image.h>
#include <stdio.h>

#include "memory.h"

resource_manager_t* resource_manager_create(SDL_Renderer* renderer) {
	if (renderer == NULL) {
		return NULL;
	}

	resource_manager_t* manager = mem_alloc(sizeof(resource_manager_t));
    
	if (manager == NULL) {
		return NULL;
	}

	memset(manager, 0, sizeof(resource_manager_t));
	manager->renderer = renderer;
	return manager;
}

void resource_manager_destroy(resource_manager_t* manager) {
	if (manager == NULL) {
		return;
	}

	for (int i = 0; i < manager->count; i++) {
		if (manager->textures[i] != NULL) {
			SDL_DestroyTexture(manager->textures[i]);
			manager->textures[i] = NULL;
		}
	}

	mem_free(manager);
}

int resource_texture_load(resource_manager_t* manager, const char* path) {
	if (manager == NULL || path == NULL) {
		return 0;
	}

	if (manager->count >= RESOURCE_MAX_TEXTURES) {
		fprintf(stderr, "ERROR: texture manager full\n");
		return 0;
	}

	SDL_Surface* surface = IMG_Load(path);

	if (surface == NULL) {
		fprintf(stderr, "ERROR: cannot load image %s: %s\n", path, IMG_GetError());
		return 0;
	}

	SDL_Texture* texture = SDL_CreateTextureFromSurface(manager->renderer, surface);
	SDL_FreeSurface(surface);

	if (texture == NULL) {
		fprintf(stderr, "ERROR: cannot create texture from %s: %s\n", path, SDL_GetError());
		return 0;
	}

	int id = manager->count;
	manager->textures[id] = texture;
	manager->count++;
	return id;
}

SDL_Texture* resource_texture_get(const resource_manager_t* manager, int id) {
	if (manager == NULL || id < 0 || id >= manager->count) {
		return NULL;
	}

	return manager->textures[id];
}