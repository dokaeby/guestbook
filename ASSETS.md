# 정원 일러스트

이미지는 내장 image_gen 도구로 새로 생성하고 육안 확인 후 JPEG로 압축했습니다. 이미지 서버·외부 폰트·유료 API를 앱 실행 중 호출하지 않습니다. PNG 원본은 생성 도구의 기본 보관 위치에 유지하고, 배포에는 아래 JPEG만 사용합니다.

| 파일 | 용도 | 해상도 | 크기 |
| --- | --- | --- | --- |
| `static/images/garden.jpg` | 상단 정원 일러스트 | 1152×768 | 266,760 bytes |
| `static/images/letter.jpg` | 작성 카드의 편지 이미지 | 480×480 | 41,031 bytes |
| `static/images/flowers.jpg` | 목록 인사 배너와 빈 목록 | 480×480 | 42,432 bytes |

합계 350,223 bytes(약 342 KiB). 중요한 상단 이미지는 우선 로딩하고, 하단 이미지는 지연 로딩합니다. 꽃 이미지를 여러 위치에서 재사용하므로 브라우저 캐시를 이용할 수 있습니다. 기존 색상·서체·16px 본문·16px 카드 모서리를 유지했습니다. 장식 이미지에는 빈 alt를, 정원 이미지에는 대체 설명을 제공합니다.

## 생성 프롬프트

- Garden: Landscape watercolor/gouache editorial illustration of a peaceful botanical garden, sage green mailbox, cream envelopes, wooden bench, white daisies, peach flowers, olive trees, sunlight and birds. Ivory open sky, detailed lower garden, soft paper grain. No people, no lettering, no logo, no watermark.
- Letter: Square watercolor/gouache still life on ivory paper: cream envelope, pressed daisy, green fountain pen, blank folded letter, leafy branch and unlettered postage stamps. Sage, white, peach, generous margins. No text, no logos, no watermark.
- Flowers: Square watercolor/gouache bouquet of white daisies and peach wildflowers in a sage ceramic vase beside a cream envelope. Ivory background, soft sunlight, paper texture, centered with margins. No people, no text, no logos, no watermark.
