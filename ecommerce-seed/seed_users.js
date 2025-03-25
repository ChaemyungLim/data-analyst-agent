const { faker } = require('@faker-js/faker');
const client = require('./db');

const USER_COUNT = 10000;
const usernameSet = new Set();
const emailSet = new Set();

(async () => {
  await client.connect();
  console.log(`Connected. Seeding ${USER_COUNT} users...`);

  let insertedCount = 0;
  let i = 0;

  while (insertedCount < USER_COUNT) {
    const username = faker.internet.username().slice(0, 20);
    const email = faker.internet.email().slice(0, 100);

    // 중복이면 건너뛰기
    if (usernameSet.has(username) || emailSet.has(email)) {
      continue;
    }

    usernameSet.add(username);
    emailSet.add(email);

    const user = {
      id: faker.string.uuid(),
      username,
      password: faker.internet.password({ length: 12 }).slice(0, 20),
      name: faker.person.fullName().slice(0, 50),
      email,
      phone: `010-${faker.number.int({ min: 1000, max: 9999 })}-${faker.number.int({ min: 1000, max: 9999 })}`,
      gender: faker.helpers.arrayElement(['M', 'F']),
      birth: faker.date.birthdate({ min: 18, max: 65, mode: 'age' }),
      address: faker.location.streetAddress().slice(0, 255)
    };

    try {
      await client.query(`
        INSERT INTO users (
          user_id, username, password_hash, name, email, phone_number,
          birth_date, gender, address, is_active, created_at, updated_at
        ) VALUES (
          $1, $2, $3, $4, $5, $6, $7, $8, $9, true, NOW(), NOW()
        )
      `, [
        user.id, user.username, user.password, user.name,
        user.email, user.phone, user.birth, user.gender, user.address
      ]);
      insertedCount++;
      if (insertedCount % 1000 === 0) {
        console.log(`Inserted ${insertedCount} users...`);
      }
    } catch (err) {
      console.error(`Error at index ${i}: ${err.message}`);
    }

    i++;
  }

  console.log("All users inserted!");
  await client.end();
})();