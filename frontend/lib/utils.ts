import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  /** Combina clases condicionales y resuelve conflictos de Tailwind CSS. */
  return twMerge(clsx(inputs))
}
