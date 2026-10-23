# 편안하고 산뜻한 정원 일러스트

이미지는 내장 image_gen 도구로 새로 생성하고 육안 확인 후 JPEG로 압축했습니다. 이미지 서버·외부 폰트·유료 API를 앱 실행 중 호출하지 않습니다. PNG 원본은 생성 도구의 기본 보관 위치에 유지하고, 배포에는 아래 JPEG만 사용합니다.

| 파일 | 용도 | 해상도 | 크기 |
| --- | --- | --- | --- |
| `static/images/garden.jpg` | 민트 우편함과 레몬나무 정원 | 1152×768 | 225,949 bytes |
| `static/images/letter.jpg` | 연두 잎과 밝은 편지 이미지 | 480×480 | 26,236 bytes |
| `static/images/flowers.jpg` | 흰색·레몬색 들꽃과 민트 화병 | 480×480 | 44,305 bytes |

합계 296,490 bytes(약 290 KiB). 빈티지한 질감과 갈색을 줄이고 민트·연두·레몬색, 아침 햇빛과 넉넉한 여백으로 편안하고 상큼한 분위기를 만들었습니다. 중요한 상단 이미지는 우선 로딩하고, 하단 이미지는 지연 로딩합니다. 꽃 이미지를 여러 위치에서 재사용하므로 브라우저 캐시를 이용할 수 있습니다. 기존 색상·서체·16px 본문·16px 카드 모서리를 유지했습니다. 장식 이미지에는 빈 alt를, 정원 이미지에는 대체 설명을 제공합니다.

## 생성 프롬프트

- Garden: Landscape 3:2 comfortable yet fresh Scandinavian watercolor/gouache garden. Mint-green mailbox and cream envelope, simple bench, delicate white daisies and pale lemon-yellow flowers, lime-green lemon tree, distant hills and a tiny bird. Airy ivory sky, gentle morning light, open upper third. No antique paper, sepia, brown, heavy grain, text, people, logos or watermark.
- Letter: Square fresh Scandinavian watercolor/gouache still life. Ivory envelope, blank card, mint pen, fresh lime-green twig, white daisy and pale lemon blossom. Pale warm white background, smooth paper, soft morning shadows, generous margins. No writing, logos, watermark, vintage parchment, brown or heavy grain.
- Flowers: Square relaxed fresh bouquet of white daisies, lemon-yellow flowers and tender green leaves in a mint ceramic vase beside a cream envelope. Airy Scandinavian watercolor/gouache, pale ivory background, morning light, soft shadows, plenty of margins. No antique paper, sepia, brown, people, lettering, logos or watermark.
