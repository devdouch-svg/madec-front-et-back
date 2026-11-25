import { z } from "zod";

/** Matches backend `app/schemas/auth.py::_validate_password_strength */
export const passwordField = z
  .string()
  .min(8, "Le mot de passe doit contenir au moins 8 caractères")
  .regex(/[A-Z]/, "Le mot de passe doit contenir au moins une majuscule")
  .regex(/[a-z]/, "Le mot de passe doit contenir au moins une minuscule")
  .regex(/\d/, "Le mot de passe doit contenir au moins un chiffre");

export const PASSWORD_HINT =
  "8 caractères minimum, avec au moins une majuscule, une minuscule et un chiffre.";
