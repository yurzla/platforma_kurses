## MODIFIED Requirements

### Requirement: Transparent API proxy
The web service SHALL proxy requests under `/api/*` to the API, forwarding the request method, query string, body, and relevant headers (including the auth cookie or `Authorization` header), and SHALL relay response cookies back to the browser. When the API responds with HTTP 401 and the browser holds a refresh cookie, the web service SHALL transparently refresh the access token and retry the request.

#### Scenario: Request forwarded
- **WHEN** a client requests `/api/v1/...` from the web service
- **THEN** the web service forwards the request to the API and returns the upstream status, body, and headers

#### Scenario: Session cookie relayed
- **WHEN** the API sets or clears an auth cookie in response to a proxied request
- **THEN** the web service relays the `Set-Cookie` header to the browser

#### Scenario: Authorization forwarded
- **WHEN** a client sends an `Authorization` header to the web service
- **THEN** the web service forwards that header to the API

#### Scenario: Access token auto-refreshed
- **WHEN** the API responds with HTTP 401 to a proxied request and the request carries a valid refresh cookie
- **THEN** the web service refreshes the token pair, retries the original request with the new access token, and relays the new cookies to the browser

#### Scenario: Refreshed token reused within one page request
- **WHEN** a page handler makes several API calls after the access token has expired
- **THEN** every subsequent call in the same request uses the refreshed access cookie
- **AND** the page renders data from all of those calls
