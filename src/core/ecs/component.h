/**
 * @file component.h
 * @brief Базовые компоненты для ECS.
 */

#ifndef COMPONENT_H
#define COMPONENT_H

#include <stdint.h>

// Максимальное количество сущностей (фиксированный пул)
#define MAX_ENTITIES 1000

/**
 * @struct Position
 * @brief Компонент позиции сущности.
 */
typedef struct Position {
	float x;
	float y;
} Position;

/**
 * @struct Velocity
 * @brief Компонент скорости сущности.
 */
typedef struct Velocity {
	float vx;
	float vy;
} Velocity;

/**
 * @struct Sprite
 * @brief Компонент спрайта (цветной прямоугольник).
 */
typedef struct Sprite {
	uint8_t r;	// красный (0-255)
	uint8_t g;	// зелёный
	uint8_t b;	// синий
	int w;		// ширина в пикселях
	int h;		// высота в пикселях
} Sprite;

#endif	// COMPONENT_H