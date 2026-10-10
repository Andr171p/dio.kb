const resetters = new Set<() => void>();

/** Регистрирует сброс стора с пользовательскими данными — при выходе из аккаунта. */
export function registerStoreReset(reset: () => void) {
  resetters.add(reset);
}

export function resetStores() {
  resetters.forEach((reset) => reset());
}
