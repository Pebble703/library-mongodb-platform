print('=== S1 分类统计 ===');
printjson(db.books.aggregate([
  { $group: { _id: '$category', book_count: { $sum: 1 }, avg_price: { $avg: '$price' }, avg_rating: { $avg: '$rating' } } },
  { $project: { book_count: 1, avg_price: { $round: ['$avg_price', 2] }, avg_rating: { $round: ['$avg_rating', 2] } } },
  { $sort: { book_count: -1 } }
]).toArray());
print('=== S2 学院借阅 Top5 ===');
printjson(db.borrow_logs.aggregate([
  { $lookup: { from: 'readers', localField: 'reader_card', foreignField: 'card_no', as: 'r' } },
  { $unwind: '$r' },
  { $group: { _id: '$r.college', borrow_count: { $sum: 1 } } },
  { $sort: { borrow_count: -1 } },
  { $limit: 5 }
]).toArray());
