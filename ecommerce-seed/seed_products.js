const { faker } = require("@faker-js/faker");
const client = require("./db");

const PRODUCT_COUNT = 1000;

// 각 카테고리에 맞는 상품 키워드 리스트
const productMap = {
  Electronics: ["스마트폰", "노트북", "모니터", "이어폰", "태블릿"],
  Fashion: ["운동화", "재킷", "셔츠", "바지", "모자"],
  "Home Appliances": ["청소기", "공기청정기", "냉장고", "전자레인지", "세탁기"],
  Books: ["소설", "자기계발서", "에세이", "잡지", "만화"],
  Toys: ["프라모델", "인형", "퍼즐", "블록", "보드게임"],
  Beauty: ["에센스", "크림", "팩트", "쿠션", "립밤"],
  Groceries: ["라면", "햇반", "참치", "과자", "두부"],
  Furniture: ["침대", "책상", "서랍장", "소파", "테이블"],
  Sports: ["운동복", "러닝화", "골프공", "라켓", "요가매트"],
  Automotive: ["엔진코팅제", "블랙박스", "방향제", "와이퍼", "세차용품"],
};

(async () => {
  await client.connect();
  console.log("Connected. Seeding products...");

  // ✅ 브랜드, 카테고리 정보 가져오기
  const res = await client.query(`
    SELECT b.brand_id, b.brand_name, b.category_id, c.name AS category_name
    FROM brands b
    JOIN categories c ON b.category_id = c.category_id
  `);
  const brands = res.rows;

  for (let i = 0; i < PRODUCT_COUNT; i++) {
    const brand = faker.helpers.arrayElement(brands);
    const categoryName = brand.category_name;
    const productKeyword = faker.helpers.arrayElement(productMap[categoryName]);
    const productName = `${brand.brand_name} ${productKeyword}`;
    const productId = faker.string.uuid();
    const price = parseFloat(
      faker.commerce.price({ min: 10000, max: 500000, dec: 0 })
    );
    const discount = faker.number.float({ min: 0, max: 0.3, precision: 0.01 });
    const stock = faker.number.int({ min: 10, max: 300 });
    const thumbnail = faker.image.urlPicsumPhotos();

    try {
      await client.query(
        `
        INSERT INTO products (
          product_id, category_id, product_name, description,
          price, discount_rate, stock_quantity, thumbnail_url,
          is_active, created_at, updated_at
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, true, NOW(), NOW()
        )
      `,
        [
          productId,
          brand.category_id, // ✅ 수정: category_id 전달
          productName,
          faker.commerce.productDescription(),
          price,
          discount,
          stock,
          thumbnail,
        ]
      );
    } catch (err) {
      console.error(`Error at row ${i}: ${err.message}`);
    }

    if (i % 200 === 0) console.log(`Inserted ${i} products...`);
  }

  console.log("All products inserted!");
  await client.end();
})();
