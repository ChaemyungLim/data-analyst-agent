const { faker } = require('@faker-js/faker');
const client = require('./db');

(async () => {
  await client.connect();
  console.log("Connected. Seeding coupons...");

  const couponList = [];

  // 1. 정액 할인 쿠폰 10개 생성
  for (let i = 0; i < 10; i++) {
    const discountAmount = faker.number.int({ min: 1000, max: 5000 });
    const minOrder = discountAmount + faker.number.int({ min: 1000, max: 5000 });

    couponList.push({
      coupon_id: faker.string.uuid(),
      code: `FIXED${i + 1}`,
      description: `${minOrder}원 이상 주문 시 ${discountAmount}원 할인`,
      discount_amount: discountAmount,
      discount_rate: 0,
      min_order_amount: minOrder,
      expiration_date: faker.date.soon({ days: faker.number.int({ min: 30, max: 60 }) })
    });
  }

  // 2. 비율 할인 쿠폰 10개 생성
  for (let i = 0; i < 10; i++) {
    const discountRate = faker.number.int({ min: 5, max: 20 });

    couponList.push({
      coupon_id: faker.string.uuid(),
      code: `RATE${i + 1}`,
      description: `${discountRate}% 할인 쿠폰`,
      discount_amount: 0,
      discount_rate: discountRate,
      min_order_amount: 0,
      expiration_date: faker.date.soon({ days: faker.number.int({ min: 30, max: 60 }) })
    });
  }

  for (const c of couponList) {
    await client.query(`
      INSERT INTO coupon (
        coupon_id, code, description,
        discount_amount, discount_rate,
        min_order_amount, expiration_date, is_active
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, true)
    `, [
      c.coupon_id,
      c.code,
      c.description,
      c.discount_amount,
      c.discount_rate,
      c.min_order_amount,
      c.expiration_date
    ]);
  }

  console.log("All coupons inserted!");
  await client.end();
})();