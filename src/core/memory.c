/**
 * @file memory.c
 * @brief Реализация безопасных обёрток памяти.
 */

#include "memory.h"

#include <stdio.h>
#include <stdlib.h>


void* mem_alloc(size_t size) {
	if (size == 0) {
		return NULL;
	}
    
	void* ptr = malloc(size);

	if (ptr == NULL) {
		fprintf(stderr, "FATAL: memory allocation of %zu bytes failed\n", size);
		exit(EXIT_FAILURE);
	}

	return ptr;
}

void mem_free(void* ptr) {
	free(ptr);
}