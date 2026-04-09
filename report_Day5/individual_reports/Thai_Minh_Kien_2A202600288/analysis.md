Sản Phẩm: Vietnam Airlines - Chatbot NEO

Path 1: NEO trả lời rõ ràng và kèm theo các đường link dẫn đến các thông tin liên quan. 

Test case: Hỏi về quy trình đi máy bay với trẻ em dưới 2 tuổi 

--> AI trả lời đúng, ngoài ra còn cung cấp thêm các thông tin tham khảo.

Path 2: Khi ko chắc, NEO yêu cầu cung cấp thêm thông tin chứ ko trả lời ngay.

Test case: Giá vé hạng thương gia là bao nhiêu?

--> AI ko trả lời ngay mà yêu cầu user cung cấp thêm thông tin như điểm đến, điểm đi.

Path 3: Khi chatbot trả lời sai, user feedback bị sai, chatbot nhận ra và sửa sai, nhưng chỉ tập trung vào phần bị sai, ko quan tâm các context xung quanh

Test case:

User: Tôi muốn đặt vé đi Hồ Chí Minh từ Hà Nội

Bot: Hãy cung cấp mã đặt chỗ hoặc mã chuyến bay

User: tôi ko có mã đặt chỗ hoặc mã chuyến bay

Bot: *Bot bắt đầu giải thích mã chuyến bay mã đặt chỗ và cách lấy.

Path 4: Khi chatbot mất tin, chatbot sẽ chuyển sang người thật để tư vấn

Test case: User: Bạn tư vấn khó hiểu quá, tôi muốn nói chuyện với người có thẩm quyền.

Bot: Hãy đợi một lát, sẽ có nhân viên tư vấn.