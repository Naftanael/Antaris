import { PageSchema } from "../page-schema/zod/contracts.js";
import type { PageIntent, PageSchemaType } from "../page-schema/types/contracts.js";
import { allowedSectionTypes, recipesByPageType, supportedPageRecipes } from "../ui-recipes/recipes.js";

const supportedRecipes = new Set<string>(supportedPageRecipes);

function slugify(value: string): string {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 64);
}

function assertAllowedSectionTypes(schema: PageSchemaType): void {
  for (const section of schema.sections) {
    if (!allowedSectionTypes.includes(section.type as (typeof allowedSectionTypes)[number])) {
      throw new Error(`Section type nao suportado: ${section.type}`);
    }
  }
}

export function buildPageSchema(intent: PageIntent): PageSchemaType {
  if (!supportedRecipes.has(intent.pageType)) {
    throw new Error(
      `Recipe nao suportada na Fase 1: ${intent.pageType}. Receitas permitidas: ${supportedPageRecipes.join(", ")}.`
    );
  }

  const recipeFactory = recipesByPageType[intent.pageType];
  const pageId = slugify(`${intent.pageType}-${intent.goal}`) || `${intent.pageType}-page`;
  const candidate = {
    ...recipeFactory(intent),
    pageId,
  };

  const schema = PageSchema.parse(candidate);
  assertAllowedSectionTypes(schema);
  return schema;
}
