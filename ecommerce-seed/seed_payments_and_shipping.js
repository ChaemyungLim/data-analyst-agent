const { faker } = require('@faker-js/faker');
const client = require('./db');

(async () => {
  await client.connect();
  console.log("Connected. Generating payment & shipping for orders...");

  // 주문 목록 가져오기
  const res = await client.query(`SELECT order_id, total_amount FROM orders`);
  const orders = res.rows;

  for (let i = 0; i < orders.length; i++) {
    const order = orders[i];

    // 결제일 생성: 90%는 7일 이상 전, 나머지는 최근 7일 이내
    const isOld = Math.random() < 0.9;
    const paymentDate = isOld
      ? faker.date.recent({ days: 360 }) // 8~360일 전
      : faker.date.recent({ days: 6 }); // 최근 7일 이내

    // 결제 상태 설정
    let paymentStatus = 'COMPLETED';
    if (!isOld) {
      paymentStatus = faker.helpers.arrayElement(['COMPLETED', 'PENDING']);
    }

    // PENDING인데 7일 이상 경과 → FAILED 처리
    const now = new Date();
    const daysSincePayment = (now - paymentDate) / (1000 * 60 * 60 * 24);
    if (paymentStatus === 'PENDING' && daysSincePayment > 7) {
      paymentStatus = 'FAILED';
    }

    // payment_method 설정
    const paymentMethod = faker.helpers.arrayElement(['CARD', 'BANK', 'KAKAO', 'NAVER']);
    const paymentId = faker.string.uuid();

    // 주문 상태도 업데이트
    let orderStatus = 'PLACED';
    if (paymentStatus === 'FAILED') {
      orderStatus = 'CANCELLED';
    }

    // 배송 관련 정보 (COMPLETED만 생성)
    let shippingInsert = false;
    let shippingData = null;

    if (paymentStatus === 'COMPLETED') {
      shippingInsert = true;
      const shippingId = faker.string.uuid();
      const carrier = faker.helpers.arrayElement(['CJ대한통운', '한진택배', '롯데택배', '우체국택배']);
      const status = faker.helpers.arrayElement(['SHIPPED', 'DELIVERED']);
      const shippedAt = faker.date.recent({ days: 5 });
      const deliveredAt = status === 'DELIVERED' ? faker.date.recent({ days: 2 }) : null;
      const trackingNumber = faker.string.alphanumeric({ length: 12 });

      shippingData = {
        shippingId,
        carrier,
        status,
        shippedAt,
        deliveredAt,
        trackingNumber
      };
    }

    try {
      // 주문 상태 업데이트
      await client.query(`
        UPDATE orders
        SET order_status = $1, updated_at = NOW()
        WHERE order_id = $2
      `, [orderStatus, order.order_id]);

      // 결제 정보 insert
      await client.query(`
        INSERT INTO payment (
          payment_id, order_id, payment_method, payment_status, amount, payment_date
        ) VALUES ($1, $2, $3, $4, $5, $6)
      `, [
        paymentId,
        order.order_id,
        paymentMethod,
        paymentStatus,
        order.total_amount,
        paymentDate
      ]);

      // 배송 정보 insert (COMPLETED인 경우만)
      if (shippingInsert && shippingData) {
        await client.query(`
          INSERT INTO shipping (
            shipping_id, order_id, tracking_number, carrier, status,
            shipped_at, delivered_at
          ) VALUES ($1, $2, $3, $4, $5, $6, $7)
        `, [
          shippingData.shippingId,
          order.order_id,
          shippingData.trackingNumber,
          shippingData.carrier,
          shippingData.status,
          shippingData.shippedAt,
          shippingData.deliveredAt
        ]);
      }
    } catch (err) {
      console.error(`Error processing order ${order.order_id}: ${err.message}`);
    }

    if (i % 500 === 0) {
      console.log(`Processed ${i} orders...`);
    }
  }

  console.log("All payment & shipping records inserted with logic!");
  await client.end();
})();