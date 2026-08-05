<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0d1117,50:1f6feb,100:388bfd&height=200&section=header&text=Kuntal%20Maity&fontSize=56&fontColor=ffffff&animation=fadeIn&fontAlignY=36&desc=Backend%20Engineer%20%7C%20Open-Source%20Contributor%20%7C%20Chaos%20Engineering&descAlignY=56&descSize=18&descColor=a5d6ff" alt="header" width="100%">

<div align="center">

[![Typing SVG](https://readme-typing-svg.demolab.com?font=Fira+Code&size=22&pause=1000&color=58A6FF&center=true&vCenter=true&width=650&lines=Java+%26+Spring+Boot+Engineer;Spring+AI+%7C+OpenAPI+%7C+Chaos+Engineering;Open-Source+Bug+Hunter+%26+Library+Author;Kolkata%2C+India+%F0%9F%87%AE%F0%9F%87%B3)](https://git.io/typing-svg)

### Backend & AI Engineer · Java / Spring Boot · Open-Source Contributor

</div>

---

## About

I'm a backend software engineer at **Tata Business Hub** (formerly Tata Nexarc), based in Kolkata. I work primarily in Java and Spring Boot, with regular forays into Go, Kotlin, and Python.

Beyond my day job, I build open-source tooling, hunt real bugs in production libraries, and contribute fixes to the Spring AI, OpenAPI/Swagger, and Go backend ecosystems. I created **HavocFlow** — an annotation-driven chaos engineering starter for Spring Boot — published to Maven Central.

---

## Open-Source Impact

<div align="center">

![Merged PRs](https://img.shields.io/badge/Merged%20Upstream%20PRs-5-2ea44f?style=for-the-badge&logo=git&logoColor=white)
![Library Releases](https://img.shields.io/badge/Library%20Releases-5-388bfd?style=for-the-badge&logo=apache-maven&logoColor=white)
![Tests Written](https://img.shields.io/badge/Tests%20Written-206%2B-f78166?style=for-the-badge&logo=junit5&logoColor=white)
![Repos Contributed](https://img.shields.io/badge/OSS%20Repos%20Contributed-10%2B-a371f7?style=for-the-badge&logo=github&logoColor=white)

</div>

> All numbers above are directly traceable to public GitHub commit history, pull-request merge records, and release tags.

| Area | What I do |
|---|---|
| Bug fixes | Trace root causes in library internals — deserialization edge cases, broken annotation processing, nil-channel races |
| Security | Identified and fixed CVE-2026-22733 (CVSS 8.2) in HavocFlow dependency tree; ThreadLocalRandom hardening; ReDoS fix |
| Tests | Added 206 tests to `chaos-spring-boot-starter`; contributed test-coverage and readability improvements to Spring AI |
| Features | Maven BOM module for swagger-core; NORCET exam platform; WebFlux / Kafka / OTel / Gateway integrations in HavocFlow |
| Code quality | SonarQube compliance fixes across multiple libraries (S106, S1148, naming, assertion clarity) |
| Libraries supported | swagger-core ⭐ 7.5k · Spring AI ⭐ 9k · OpenAI Java ⭐ 1.5k · RudderStack ⭐ 4.5k |

---

## Open-Source Contributions

### Merged

| Project | Contribution | Link |
|---|---|---|
| **swagger-api/swagger-core** ⭐ 7.5k | Introduced a **Maven BOM module** (`swagger-bom/pom.xml`) so consumers can manage all `io.swagger.core.v3` artifacts without specifying versions; includes integration tests and Sonatype Central publishing profile | [PR #4987](https://github.com/swagger-api/swagger-core/pull/4987) |
| **swagger-api/swagger-core** | Fixed **validation meta-annotations not being processed** — `@Valid` and constraint annotations on method parameters were silently dropped during schema resolution | [PR #4986](https://github.com/swagger-api/swagger-core/pull/4986) |
| **swagger-api/swagger-core** | Removed `System.out` / `printStackTrace` across the codebase to align with SonarQube rules S106 and S1148 | [PR #4988](https://github.com/swagger-api/swagger-core/pull/4988) |
| **spring-projects/spring-ai** ⭐ 9k | Improved test readability in `OpenAiChatModelMutateTests` — Sonar naming, assertion clarity, minor duplication removed; commit accepted into main | [Commit](https://github.com/spring-projects/spring-ai/commit/fa68d1e835ee86c843ff452b1b86920f6a50ca2c) |
| **spring-ai-community/spring-ai-session** | Fixed **AWS Bedrock Converse `ValidationException`** — `SessionMemoryAdvisor` was storing empty `AssistantMessage` frames (emitted at end of tool-call sequences), which Bedrock rejected on replay; PR cherry-picked into main | [PR #19](https://github.com/spring-ai-community/spring-ai-session/pull/19) |

### Under Review

| Project | Contribution |
|---|---|
| [openai/openai-java](https://github.com/openai/openai-java/pull/771) ⭐ 1.5k | Fixed `OrganizationCostsResult.Amount.value()` throwing `OpenAIInvalidDataException` — live API returns numbers as quoted JSON strings (e.g. `"0E-6176"`); added a type-coercing deserializer |
| [spring-projects/spring-ai](https://github.com/spring-projects/spring-ai/pull/6557) ⭐ 9k | Fixed two independent null/empty `ToolContext` validation bugs in `MethodToolCallback` and `ToolCallingManager` |
| [spring-projects/spring-ai](https://github.com/spring-projects/spring-ai/pull/6330) | Fixed `FactCheckingEvaluator` and `RelevancyEvaluator` hardcoding `feedback` to empty string and discarding the raw LLM response |
| [rudderlabs/rudder-server](https://github.com/rudderlabs/rudder-server/pull/7106) ⭐ 4.5k | Fixed file descriptor leak in `Handle.upload()` — `outputFile` opened via `os.Open` was never closed on either the success or error path |
| [rudderlabs/rudder-server](https://github.com/rudderlabs/rudder-server/pull/7069) | Prevented nil-channel send DoS in `RequestHandler` — a nil channel send blocked an HTTP worker goroutine indefinitely |
| [swagger-api/swagger-core](https://github.com/swagger-api/swagger-core/pull/5184) | Added Java 8 `java.time.*` format support per the OpenAPI Formats Registry |
| [swagger-api/swagger-core](https://github.com/swagger-api/swagger-core/pull/5183) | Allow `@ExampleObject` values to be loaded from a classpath or filesystem file |

---

## Created Projects

### [HavocFlow — chaos-spring-boot-starter](https://github.com/havocflow/chaos-spring-boot-starter)

> Annotation-driven chaos engineering library for Spring Boot — authored entirely from scratch, published to Maven Central.

**What it does:** Drop `@InjectChaos` on any Spring bean method to inject latency, exceptions, or connection exhaustion under configurable failure rates — without touching production code. Designed for resilience testing in CI and staging environments.

**Technical highlights:**

- `@InjectChaos` / `@SuppressChaos` AOP annotations — method-level chaos with scenario inheritance and inline overrides
- **WebFlux support** — `ChaosWebFilter` for non-blocking HTTP fault injection via `Mono.delay()`; suppressed automatically when Spring Cloud Gateway is present to avoid double-injection
- **Ramp-up calculator** — linear `failureRate` interpolation over a configurable time window for gradual load testing
- **Ecosystem integrations** — Spring Kafka listener chaos · OpenTelemetry span events · Slack/webhook notifications · Spring Cloud Gateway reactive filter · Testcontainers lifecycle hooks
- **Security hardening** — fixed CVE-2026-22733 (CVSS 8.2, CloudFoundry Actuator auth bypass in dependency); `HashMap → ConcurrentHashMap` for thread safety; `Random → ThreadLocalRandom`; ReDoS fix in `antMatch()`; `volatile` flag for JVM visibility; overflow guard in `LatencyParser`
- **206 tests, 0 failures** — full unit and integration coverage across all strategies and integrations
- **Java 8+ · Spring Boot 2.x and 3.x compatible** · Published to Maven Central at `io.github.havocflow:chaos-spring-boot-starter`
- 5 releases: `v01.01.00` → `v01.04.01`

```xml
<dependency>
  <groupId>io.github.havocflow</groupId>
  <artifactId>chaos-spring-boot-starter</artifactId>
  <version>01.04.01</version>
</dependency>
```

---

### norcetIQ *(private)*

Full-stack exam-preparation platform for NORCET. Go backend serves a dynamically configurable set of 12 tools across 6 NORCET exam versions via a `/api/v1/norcetIq/toolsConfig` REST endpoint, with thread-safe in-memory caching using `sync.RWMutex`. TypeScript/React frontend fetches the tool catalogue at runtime, making the tool set reconfigurable without a frontend redeploy.

---

## Technology Stack

<div align="center">

[![Java](https://skillicons.dev/icons?i=java)](https://skillicons.dev)
[![Kotlin](https://skillicons.dev/icons?i=kotlin)](https://skillicons.dev)
[![Go](https://skillicons.dev/icons?i=go)](https://skillicons.dev)
[![Python](https://skillicons.dev/icons?i=python)](https://skillicons.dev)
[![TypeScript](https://skillicons.dev/icons?i=ts)](https://skillicons.dev)
[![Spring](https://skillicons.dev/icons?i=spring)](https://skillicons.dev)
[![Maven](https://skillicons.dev/icons?i=maven)](https://skillicons.dev)
[![Docker](https://skillicons.dev/icons?i=docker)](https://skillicons.dev)
[![PostgreSQL](https://skillicons.dev/icons?i=postgres)](https://skillicons.dev)
[![MySQL](https://skillicons.dev/icons?i=mysql)](https://skillicons.dev)
[![Elasticsearch](https://skillicons.dev/icons?i=elasticsearch)](https://skillicons.dev)
[![Git](https://skillicons.dev/icons?i=git)](https://skillicons.dev)
[![GitHub](https://skillicons.dev/icons?i=github)](https://skillicons.dev)
[![Linux](https://skillicons.dev/icons?i=linux)](https://skillicons.dev)

</div>

---

## GitHub Statistics

<div align="center">

<img src="https://github-profile-summary-cards-theta.vercel.app/api/cards/stats?username=kuntal1461&theme=github_dark" height="170" alt="GitHub Stats">
&nbsp;&nbsp;
<img src="https://github-profile-summary-cards-theta.vercel.app/api/cards/repos-per-language?username=kuntal1461&theme=github_dark" height="170" alt="Top Languages">

</div>

<div align="center">

<img src="https://streak-stats.demolab.com?user=kuntal1461&theme=github-dark-blue&hide_border=true&stroke=388bfd&ring=388bfd&fire=f78166&currStreakLabel=a5d6ff" alt="Contribution Streak" width="500">

</div>

---

## Contribution Activity

<div align="center">

<img src="https://github-readme-activity-graph.vercel.app/graph?username=kuntal1461&theme=github-compact&bg_color=0d1117&color=58a6ff&line=388bfd&point=f78166&area=true&hide_border=true" alt="Contribution Activity Graph" width="100%">

</div>

---

## Profile Summary

<div align="center">

<img src="https://github-profile-summary-cards-theta.vercel.app/api/cards/profile-details?username=kuntal1461&theme=github_dark" alt="Profile Summary" width="100%">

</div>

---

## Contribution Snake

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/kuntal1461/kuntal1461/output/github-contribution-grid-snake-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="https://raw.githubusercontent.com/kuntal1461/kuntal1461/output/github-contribution-grid-snake.svg">
  <img alt="Contribution Snake" src="https://raw.githubusercontent.com/kuntal1461/kuntal1461/output/github-contribution-grid-snake.svg" width="100%">
</picture>

</div>

> **Setup:** See `.github/workflows/snake.yml` in this repository. The snake regenerates weekly. You must enable **Actions** and the `output` branch will be created automatically on first run.

---

## Contact

<div align="center">

[![LinkedIn](https://img.shields.io/badge/LinkedIn-kuntal--maity-0a66c2?style=for-the-badge&logo=linkedin&logoColor=white)](https://linkedin.com/in/kuntal-maity)
[![Email](https://img.shields.io/badge/Email-kuntal.1461%40gmail.com-ea4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:kuntal.1461@gmail.com)
[![GitHub](https://img.shields.io/badge/GitHub-kuntal1461-24292f?style=for-the-badge&logo=github&logoColor=white)](https://github.com/kuntal1461)

</div>

---

<div align="center">

![Profile Views](https://komarev.com/ghpvc/?username=kuntal1461&color=388bfd&style=flat-square&label=Profile+Views)

</div>

<div align="center">

*I fix things that are broken in production and build things that are worth building.*

</div>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:388bfd,50:1f6feb,100:0d1117&height=120&section=footer" alt="footer" width="100%">
