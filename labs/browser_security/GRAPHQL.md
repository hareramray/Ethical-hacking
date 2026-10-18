# GraphQL authorization and bounded query validation

This runnable lesson uses the real `graphql-core` parser, schema validator and synchronous executor. It compares two resolver policies over two disposable stores containing fictional blue and amber tenant notebooks. All snippets are server-owned fixtures; there is no arbitrary-query endpoint or external GraphQL target.

Start the lab using [the setup instructions](README.md), open the main page, and choose **GraphQL authorization**. Select a fixture and click **Compare resolver permissions**. Inspect the selected document, variables, GraphQL `data` and `errors`, resolver count, and notebook titles before and after execution.

## Seven runnable fixtures

| Fixture | Vulnerable execution | Fixed execution |
| --- | --- | --- |
| Allowed read | Returns the blue document marker. | Returns the same permitted marker without errors. |
| Nested tenant relation | An allowed blue parent exposes its related amber document. | The nested resolver refuses amber; the blue parent remains, with `relatedDocument: null` and a path-specific error. |
| Protected field | A member reads the fictional administrator note on an allowed object. | The title remains available, while `adminNote` is null with a field-permission error. |
| Own-document mutation | Renames Ada's own blue document once. | Performs the same authorized write; positive evidence that the repair preserves useful mutations. |
| Forbidden mutation | Renames the other tenant's amber document. | Verifies tenant and ownership before writing; zero writes and identical before/after titles. |
| Two aliases | Returns both the permitted and foreign document. | Checks each root resolver independently, returning `own` and refusing `other`. The error path uses the response alias `other`. |
| Query budget | Resolves eight harmless aliases and their scalar fields: 24 field resolver calls. | A real AST validation rule rejects 24 selected field nodes against a limit of 12 before any resolver executes. |

The fictional identity is Ada, a member of tenant blue. The server supplies that identity; browser input cannot select a role, tenant, document ID, custom query, variables or comparison mode. The two stores are freshly copied for every request and every mode. Mutations affect only that disposable copy and never write a database or file.

## Inspect the important boundaries

The nested fixture runs this GraphQL document:

```graphql
query Nested {
  document(id: "blue-note") {
    id
    relatedDocument {
      id
      marker
    }
  }
}
```

The root blue document is permitted. That decision says nothing about the tenant of `relatedDocument`. The fixed nested resolver checks the target object before returning it. The schema deliberately makes the relation and protected field nullable, so you can observe allowed data and permission errors together. A different schema's non-null fields can propagate null to a parent; this fixture does not demonstrate every nullability shape.

The mutation resolver checks both tenant and ownership before changing a title. Compare the actual `writes`, `before`, and `after` values rather than inferring safety from the response alone. A read permission does not automatically confer write permission.

Aliases create multiple selections inside **one** GraphQL operation. They do not create HTTP request batching, and the lesson does not claim to test batching. The executor invokes each document resolver, which independently authorizes its selected object. The fixed alias result preserves the permitted sibling even when another sibling fails authorization.

The field budget is an additional `graphql-core` validation rule, alongside the standard schema rules. The fixed path calls validation before `execute_sync`; a middleware counter measures actual resolver invocations. The budget fixture proves rejection with `validationPassed: false`, `data: null`, a `FIELD_BUDGET_EXCEEDED` error, zero resolver calls, and zero permission checks or writes. This is a deliberately simple count of field nodes in these fixed, fragment-free documents. It is **not** a production complexity estimator: it does not model list cardinality, resolver costs, fragment expansion, conditional directives, query depth or total work across HTTP batches.

The UI posts only a fixture ID to the CSRF-protected `/api/graphql/compare/` endpoint. HTTP 200 means the comparison was delivered; each mode's GraphQL `data` and `errors` separately describe execution. This wrapper is not a general implementation of the GraphQL-over-HTTP protocol. All displayed values use inert Vue text interpolation.

## Verification

From `labs/browser_security/backend`, after installing the lab requirements:

```powershell
..\.venv\Scripts\python.exe manage.py test securitylab.test_graphql_lab
```

For browser checks, stop the launcher so ports 8766 and 8767 are free. From `labs/browser_security/frontend`:

```powershell
npm run build
$env:LAB_BROWSER_CHANNEL = 'chrome'
npx playwright test tests/graphql.spec.js
```

Playwright starts its own local test servers. Backend checks cover the legitimate read and mutation, nested and field permissions, authorized administrator field access, same-tenant ownership denial, alias-specific error paths, actual query-budget rejection, independent stores, strict inputs, CSRF and origin checks. Browser checks compare rendered JSON against actual HTTP responses and verify real store changes, no writes on refusal, reset behavior, malformed-response handling and abandoned-request cleanup.

## Scope and next exercises

This lesson extends the object authorization concepts in the [web application tutorial](../../tutorials/11-web-application-security.md) and [API security tutorial](../../tutorials/12-api-security-and-modern-authentication.md). It complements [the learning roadmap](../../ETHICAL_HACKING_ROADMAP.md).

It does not implement an authentication provider, subscriptions, HTTP batching, persisted queries, introspection policy, federation, DataLoader caches, pagination, generalized cost limits or per-user rate limits. No fixture creates expensive work: the largest fixed document resolves eight tiny in-memory objects. In a larger service, shared authorization functions must cover every route to an object and field, and resource controls must account for the schema and resolver behavior.

Primary references: [GraphQL authorization guidance](https://graphql.org/learn/authorization/) explains placing authorization in application/business logic; [GraphQL security guidance](https://graphql.org/learn/security/) discusses depth, breadth and query complexity; [graphql-core validation](https://graphql-core-3.readthedocs.io/en/stable/modules/validation.html) and [execution](https://graphql-core-3.readthedocs.io/en/stable/modules/execution.html) document the actual engine used here. The lab pins [graphql-core 3.3.0](https://pypi.org/project/graphql-core/3.3.0/).
