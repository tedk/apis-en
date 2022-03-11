# Notes for developers

The security of nomic depends on being able to receive all relevant
policies for a resource. Most policies carry various ways of denying
access; if one of these fails to reach the policy evaluator, its
contraint will not be applied. The only place we provide an Allow
policy is in nomic-server's account requirements response (allow if
account matches) along with IP restrictions and the like. Since nomic
requires at least one matching Allow policy, we gain a bit of security
against a hypothetical bug that would cause the policies from
nomic-server to be ignored. Additionally, we deny the video response
if any policy could not be retrieved or computed.

## Client security

Two of the policy components are weak because they rely on cooperation
of the client: Domain restriction uses the Origin header to determine
the embedding website, and georestriction trusts the X-Forwarded-For
header to determine the user's real public IP address.

The weak client-cooperation security policies are subject to two types
of threat, both of which are impossible to fully protect against:

1. A technically savvy viewer trying to watch (or download) a video
   while bypassing restrictions (geo, domain), or
2. A developer building a website to allow non-savvy viewers to watch
   customer videos while bypassing restrictions.

We have attempted to optimize for scenario 2 with its larger
exposure. Georestriction and domain restriction would both require a
scenario 2 developer to proxy calls to Wedge Playback, which would
make them easier to block if discovered.

Scenario 1 on the other hand is a lost cause; a user may use browser
extensions to forge Origin headers to bypass domain restriction and
X-Forwarded-For to bypass georestriction.

## Policy sources

Note that only weak or trivial policies are carried on the key; strong
policies (TVE, IP) are derived from the account. Domain restriction is
carried on the key because it varies by player, and account ID is
baked into the key only to keep it from being used by other accounts.

There's another reason the policies that are permitted to be on a
policy key are limited: Many of the policies nomic deals in (such as
georestriction) are paid features. If we allowed customer to create
arbitrary policy keys, they would be able to use these features
without paying for them.

## Extending the policy language

When writing a new primitives, be aware of the difference between *not
matching* and *yielding false*. For example, the `!adobe-tve-valid`
primitive treats auth credential context keys as optional so that it
can still yield `true` (to deny the request) when credentials are
missing. If it failed to treat them as optional, missing credentials
would cause the match to fail and the Deny effect would be lost.

In general, any time a primitive is added the inverse primitive should
also be added. We do not have a generic `not` primitive to use in the
policy language because the match-reasons semantics are complicated.

The following keywords are reserved and not allowed to be primitive
policy predicate names: `and`, `or`, `not`, `constant`.

## Policy key format

A policy key string consists of the fixed four-byte header `"BCpk"`,
followed by an encrypted body.

The unencrypted body contains, in order:

* The single byte `1`, where the 1 denotes version 1 of the key format
* Exactly 16 random bytes (128 bits of entropy)
* The JSON SMILE representation of a payload map in the short policy
  format ("key-data" format)

The body is encrypted using Keyczar's AES+HMAC-SHA1, and the result is
base64-encoded using the "URL and filename safe alphabet" variant
(with `_` and `-`). There is a single common encryption key shared
between nomic-server and wedge-server.  Should it be necessary to do
so, we can rotate this key (without decomissioning existing keys)
using Keyczar's keystore management.

## Future work

### Policy store

We would like to support more complex policies that would be stored on
the Nomic server and referenced by its API with an id. The API as uses
account IDs as a security principal but we may choose something else
for implementation; by default policies would be partitioned by
account like other BC resources.

We do not yet have a plan for which policy features may be used in
this API and how we check for entitlements to use them.

The API would support CRUD operations on policies, identified by ID
(autogenerated UUID) or reference ID, and would likely be routed under
`/v_/accounts/:account-id/policies` and authorized/gated through
Wedge. We do not know what the semantics of reference IDs would be,
such as how we would enforce uniqueness.

Player policy keys will then be expanded to allow policy ID
references. The short policy format is `{"policy-id": "<policy-id>"}`,
where `<policy-id>` is the UUID or refid of a policy entity.

### Key management and revocation

We do not have a have to revoke a policy key that is being
misused. When a key is created, we don't keep a record of it, and we
don't have a store in which to list revocations. See the
https://jira.brightcove.com/browse/EN-462 Epic for plans.

At minimum, we will need to provide an API for listing existing keys
and for revoking a single key (and possibly unrevoking it.)

### Video ID policy restrictions

We'd like to re-enable video ID restrictions for player policy
keys. (They can be represented by policies but cannot be bake dinto
keys.) Before we can re-enable this we will need a good way to verify
the video belongs to the account permitted by the Cathy token or other
authorizer.

The short policy format is `{"video-id": "<id>"}` where `<id>` is a
string representing a video ID or possibly refid.  This represents the
policy "if request video ID is not equal to `<id>`, deny". Although we
would dereference a refid on the video request to see if it matched a
policy bearing a canonical video ID, it is not clear if we would
support a mismatch the other direction.

### Resource policy API

The resource API would be a private API used by Wedge to retrieve the
policy object controlling access to a given resource.

`GET /v_/policies/for/*` would yield everything nomic-server knows
about a policy governing the resource named by the resource URL path
in the `*` component of the URL (everything following `/for/`).