import asyncio
import random
import time
import traceback
import json
import os
import logging
import sys

# import pyperclip # Có thể không cần nếu không dùng copy/paste
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from utils import hide_process, initialize, log_message, run_as_trusted, smooth_scroll, type_text_input

# Import SocketIO AsyncClient
from socketio import AsyncClient

# Khởi tạo SocketIO client
sio = AsyncClient()

# Lưu trữ các bot instances đang chạy
running_bots = {}

# Constants (Giữ nguyên)
COMMENTS = [
    "Danh sách ứng viên trên Timviec365 thật sự rất chất lượng!",
    "Bạn nào đã sử dụng Timviec365 chưa? Đánh giá thế nào?",
    "Công cụ tìm ứng viên của Timviec365 rất tiện lợi, dễ sử dụng!",
    "Mình đã tìm được ứng viên phù hợp trên Timviec365, mọi người thử xem nhé!",
    "Trang web này rất hữu ích cho ai đang tìm việc!",
    "Bạn đã thử tìm việc trên Timviec365 chưa? Hãy chia sẻ trải nghiệm của bạn!",
    "Cảm ơn Timviec365 đã giúp tôi tìm được công việc phù hợp!",
    "Có ai có kinh nghiệm sử dụng Timviec365 không?",
    "Tìm việc nhanh chóng và hiệu quả trên Timviec365!",
    "Mọi người đã tìm được công việc tốt trên Timviec365 chưa?",
    "Cần tìm việc gấp, ai có kinh nghiệm chỉ giúp với!",
    "Làm thế nào để nâng cao hồ sơ ứng tuyển trên Timviec365?",
    "Timviec365 có những ưu điểm gì so với các trang tìm việc khác?",
    "Bạn có biết cách tối ưu CV để tăng cơ hội phỏng vấn không?",
    "Timviec365 có hỗ trợ ứng viên mới không?",
    "Mình đã nhận được nhiều cơ hội nhờ Timviec365, cảm ơn rất nhiều!",
    "Làm sao để tìm được công việc phù hợp với kỹ năng của mình?",
    "Có ai đã thành công tìm việc qua Timviec365 chưa?",
    "Bạn có kinh nghiệm gì khi phỏng vấn không?",
    "Chia sẻ mẹo giúp ứng tuyển thành công trên Timviec365 nhé!"
]

SHARE_POSTS = [
    "Cơ hội việc làm tuyệt vời! Hãy thử ngay trên Timviec365!",
    "Bạn đang tìm kiếm công việc? Timviec365 có thể giúp bạn!",
    "Nhiều cơ hội việc làm hấp dẫn đang chờ bạn trên Timviec365!",
    "Hãy chia sẻ công cụ hữu ích này đến bạn bè của bạn!",
    "Timviec365 - nơi giúp bạn kết nối với nhà tuyển dụng nhanh chóng!",
    "Bạn đã tìm việc hôm nay chưa? Đừng bỏ lỡ cơ hội trên Timviec365!",
    "Công cụ tìm việc miễn phí và hiệu quả trên Timviec365!",
    "Chia sẻ ngay để bạn bè của bạn cũng tìm được việc làm phù hợp!",
    "Nhiều công ty đang tuyển dụng trên Timviec365, đừng bỏ lỡ!",
    "Timviec365 giúp bạn dễ dàng tìm kiếm công việc phù hợp!",
    "Ứng tuyển nhanh chóng, không mất thời gian!",
    "Hàng ngàn việc làm mới được cập nhật mỗi ngày trên Timviec365!",
    "Bạn đang muốn thay đổi công việc? Hãy thử ngay Timviec365!",
    "Nhà tuyển dụng đang chờ đón bạn! Ứng tuyển ngay trên Timviec365!",
    "Hỗ trợ ứng viên tìm việc miễn phí và dễ dàng!",
    "Chia sẻ kinh nghiệm tìm việc hiệu quả trên Timviec365!",
    "Timviec365 giúp bạn kết nối với nhà tuyển dụng một cách nhanh chóng!",
    "Bạn đã thử tìm việc bằng Timviec365 chưa? Kết quả sẽ bất ngờ đấy!",
    "Hãy bắt đầu sự nghiệp mới của bạn ngay trên Timviec365!"
]

REACTIONS = [
    {"name": "Like", "xpath": '//div[@aria-label="Thích"] | //div[@aria-label="Like"]'},
    {"name": "Love", "xpath": '//div[@aria-label="Yêu thích"] | //div[@aria-label="Love"]'},
    {"name": "Care", "xpath": '//div[@aria-label="Thương thương"] | //div[@aria-label="Care"]'},
    {"name": "Haha", "xpath": '//div[@aria-label="Haha"]'},
    {"name": "Wow", "xpath": '//div[@aria-label="Wow"]'},
    {"name": "Sad", "xpath": '//div[@aria-label="Buồn"] | //div[@aria-label="Sad"]'},
    {"name": "Angry", "xpath": '//div[@aria-label="Phẫn nộ"] | //div[@aria-label="Angry"]'}
]

CONTENT_POST = [
    "Hãy để đam mê dẫn lối, chúng tôi đang tìm kiếm những tài năng sáng tạo, nhiệt huyết và muốn thách thức bản thân. Ứng tuyển ngay để mở ra cơ hội mới, khám phá tiềm năng vô hạn và cùng chúng tôi tạo nên những điều tuyệt vời trong tương lai!",
    "Bạn đã sẵn sàng cho hành trình mới? Một công việc tuyệt vời đang chờ đón bạn tại đây. Không chỉ là công việc, chúng tôi mang đến một môi trường giúp bạn phát triển và xây dựng sự nghiệp. Tham gia ngay và cùng nhau bứt phá giới hạn!",
    "Hãy đến với chúng tôi và khám phá những cơ hội tuyệt vời mà bạn không thể bỏ lỡ! Chúng tôi tin rằng với sự nỗ lực và đam mê của bạn, mọi giới hạn sẽ bị phá vỡ. Đăng ký ngay để trở thành một phần của đội ngũ thành công!",
    "Công việc trong mơ không còn xa, nó đang ở ngay trước mắt bạn! Chúng tôi đang tìm kiếm những ứng viên đầy nhiệt huyết, sáng tạo và sẵn sàng đón nhận thử thách. Cùng nhau, chúng ta sẽ chinh phục những đỉnh cao mới trong sự nghiệp!",
    "Gia nhập đội ngũ của chúng tôi là cơ hội để bạn phát triển bản thân và xây dựng sự nghiệp. Với môi trường làm việc năng động, thân thiện và đầy cơ hội thăng tiến, hãy cùng nhau tạo ra sự thay đổi lớn lao! Đừng bỏ lỡ, ứng tuyển ngay!",
    "Chúng tôi đang tìm kiếm những tài năng xuất sắc, sáng tạo và đam mê với công việc. Nếu bạn muốn thử thách bản thân trong một môi trường đầy năng động và cơ hội, đừng chần chừ, hãy gửi hồ sơ của bạn ngay hôm nay để cùng chúng tôi tiến xa hơn!",
    "Cơ hội không đến nhiều lần! Chúng tôi đang tìm kiếm những cá nhân tài năng, có đam mê và sẵn sàng đối mặt với thách thức mới. Hãy tham gia vào đội ngũ của chúng tôi để cùng nhau chinh phục những mục tiêu mới, xây dựng tương lai rực rỡ!",
    "Một hành trình sự nghiệp đầy triển vọng đang mở ra trước mắt bạn. Chúng tôi mang đến cơ hội phát triển bản thân và làm việc trong môi trường sáng tạo. Đừng ngại thử thách bản thân và ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội tuyệt vời này!",
    "Chúng tôi đang tìm kiếm những người bạn đồng hành đam mê, nhiệt huyết và sáng tạo để cùng nhau đạt được thành công. Đừng bỏ lỡ cơ hội này, gửi ngay hồ sơ của bạn và bước vào hành trình phát triển sự nghiệp đáng nhớ cùng chúng tôi!",
    "Đôi khi, cơ hội đến từ những điều bất ngờ. Hãy sẵn sàng cho một công việc mới đầy thú vị tại công ty chúng tôi. Môi trường làm việc thân thiện, sáng tạo và cơ hội thăng tiến luôn chờ đón bạn. Đừng bỏ qua, hãy ứng tuyển ngay!",
    "Bạn đã sẵn sàng bứt phá giới hạn? Một công việc thú vị trong môi trường đầy sáng tạo đang chờ đón bạn. Cùng chúng tôi chinh phục những đỉnh cao mới trong sự nghiệp và khám phá tiềm năng của bản thân. Ứng tuyển ngay để không bỏ lỡ!",
    "Chúng tôi tin rằng sự sáng tạo và nhiệt huyết của bạn sẽ là chìa khóa mở ra cánh cửa thành công trong công việc. Đừng bỏ lỡ cơ hội làm việc cùng một đội ngũ đầy tài năng và tận tâm. Ứng tuyển ngay hôm nay để khởi đầu hành trình mới!",
    "Công việc thú vị với những thách thức mới đang chờ đón bạn. Hãy tham gia đội ngũ của chúng tôi và cùng nhau khám phá những cơ hội phát triển không giới hạn. Đừng để tuột mất cơ hội này, ứng tuyển ngay và trở thành một phần của thành công!",
    "Nếu bạn đang tìm kiếm một môi trường làm việc sáng tạo, đầy thử thách và cơ hội phát triển, chúng tôi chính là điểm đến của bạn. Hãy nắm bắt cơ hội này và cùng chúng tôi xây dựng tương lai sự nghiệp vững chắc. Đăng ký ngay hôm nay!",
    "Mọi hành trình đều bắt đầu từ bước đi đầu tiên, và chúng tôi đang chờ đón bước đi của bạn. Cơ hội phát triển sự nghiệp không giới hạn đang mở ra tại đây, đừng bỏ lỡ, hãy gửi ngay hồ sơ của bạn để cùng chúng tôi tạo nên điều khác biệt!",
    "Sự nghiệp của bạn có thể phát triển vượt bậc khi bạn nắm bắt cơ hội. Chúng tôi đang tìm kiếm những ứng viên sáng tạo, nhiệt huyết và muốn phát triển bản thân. Hãy đến và khám phá cơ hội không giới hạn tại công ty chúng tôi. Ứng tuyển ngay!",
    "Thành công không đến từ việc chờ đợi, mà từ những hành động thiết thực. Hãy nắm bắt ngay cơ hội việc làm tuyệt vời tại công ty chúng tôi và cùng nhau tạo ra những giá trị đích thực. Ứng tuyển ngay hôm nay để trở thành một phần của đội ngũ!",
    "Bạn đang tìm kiếm một công việc mới, đầy thách thức và cơ hội phát triển? Hãy đến với chúng tôi, nơi sự sáng tạo và đam mê được trân trọng. Chúng tôi luôn chào đón những tài năng nhiệt huyết. Ứng tuyển ngay để không bỏ lỡ cơ hội!",
    "Tương lai sự nghiệp của bạn bắt đầu ngay hôm nay! Chúng tôi đang tìm kiếm những ứng viên tài năng và sáng tạo để cùng nhau xây dựng tương lai. Đừng chần chừ, hãy gửi hồ sơ của bạn ngay và gia nhập đội ngũ tuyệt vời của chúng tôi!",
    "Bạn đang tìm kiếm cơ hội phát triển sự nghiệp trong một môi trường chuyên nghiệp và năng động? Chúng tôi có vị trí dành cho bạn! Hãy cùng nhau khám phá và chinh phục những thử thách mới. Ứng tuyển ngay để không bỏ lỡ cơ hội tuyệt vời!",
    "Bạn có muốn trở thành một phần của đội ngũ tài năng và nhiệt huyết? Hãy tham gia cùng chúng tôi và khám phá những cơ hội phát triển bản thân không giới hạn. Đừng để lỡ cơ hội việc làm này, hãy ứng tuyển ngay và bắt đầu hành trình mới!",
    "Mỗi ngày đều là một cơ hội để bạn khám phá bản thân và phát triển sự nghiệp. Hãy đến với chúng tôi và cùng nhau tạo dựng tương lai tươi sáng hơn. Ứng tuyển ngay hôm nay để không bỏ lỡ những cơ hội phát triển không giới hạn!",
    "Bạn có sẵn sàng chinh phục những thử thách mới và khám phá tiềm năng bản thân? Chúng tôi đang tìm kiếm những ứng viên đam mê và tài năng như bạn. Hãy gửi hồ sơ ngay hôm nay để cùng chúng tôi xây dựng sự nghiệp vững chắc và thành công!",
    "Sự nghiệp của bạn chỉ cách một bước đi! Chúng tôi đang tìm kiếm những người đam mê, sáng tạo và sẵn sàng đối mặt với thách thức mới. Đừng bỏ lỡ cơ hội này, ứng tuyển ngay để trở thành một phần của đội ngũ đầy tài năng và nhiệt huyết!",
    "Bạn có muốn phát triển sự nghiệp trong một môi trường năng động và chuyên nghiệp? Chúng tôi đang chờ đón bạn! Hãy tham gia đội ngũ của chúng tôi và cùng nhau tạo ra những giá trị khác biệt. Ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội!",
    "Chúng tôi tin rằng bạn chính là mảnh ghép còn thiếu của đội ngũ chúng tôi! Hãy ứng tuyển ngay hôm nay để có cơ hội phát triển bản thân và sự nghiệp trong một môi trường đầy sáng tạo, thử thách và cơ hội thăng tiến. Đừng bỏ lỡ!",
    "Đừng để những cơ hội quý giá trôi qua! Hãy ứng tuyển ngay vào vị trí chúng tôi đang tìm kiếm và cùng nhau chinh phục những thử thách mới trong sự nghiệp. Môi trường làm việc thân thiện, sáng tạo và nhiều cơ hội thăng tiến đang chờ đón bạn!",
    "Bạn đã sẵn sàng cho những thử thách mới? Chúng tôi đang tìm kiếm những tài năng nhiệt huyết và sáng tạo để cùng nhau đạt được thành công. Ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển bản thân và sự nghiệp của bạn!",
    "Cơ hội việc làm tuyệt vời chỉ cách bạn một bước! Hãy tham gia đội ngũ của chúng tôi và khám phá những thử thách mới, cơ hội thăng tiến trong một môi trường sáng tạo và thân thiện. Đừng bỏ qua, ứng tuyển ngay hôm nay!",
    "Thành công bắt đầu từ một cơ hội. Hãy để chúng tôi cùng bạn thực hiện ước mơ sự nghiệp của mình. Chúng tôi đang tìm kiếm những người đam mê và tài năng. Ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển cùng chúng tôi!",
    "Bạn đang tìm kiếm một công việc thú vị với nhiều cơ hội phát triển? Hãy đến với chúng tôi và cùng nhau",
    "Chúng tôi đang tìm kiếm những tài năng đầy nhiệt huyết, sáng tạo và khao khát khám phá những thử thách mới. Đừng bỏ lỡ cơ hội phát triển bản thân tại môi trường làm việc năng động và thân thiện này. Hãy ứng tuyển ngay hôm nay để cùng chúng tôi tạo nên thành công!",
    "Bạn đã sẵn sàng bước vào hành trình sự nghiệp mới? Cùng chúng tôi chinh phục những thử thách, phát triển bản thân và xây dựng tương lai vững chắc. Đừng chần chừ, cơ hội không đến hai lần. Ứng tuyển ngay hôm nay để trở thành một phần của đội ngũ thành công!",
    "Hãy gia nhập đội ngũ của chúng tôi và khám phá những cơ hội phát triển không giới hạn. Chúng tôi luôn chào đón những cá nhân tài năng, đam mê và sẵn sàng đương đầu với thử thách. Hãy ứng tuyển ngay để cùng nhau tạo nên những thành công đột phá!",
    "Bạn có muốn trở thành một phần của môi trường làm việc sáng tạo, đầy thử thách và cơ hội? Hãy nắm bắt cơ hội việc làm tuyệt vời này và gia nhập đội ngũ của chúng tôi để phát triển sự nghiệp trong một tương lai tươi sáng hơn!",
    "Công việc trong mơ đang chờ đợi bạn! Chúng tôi đang tìm kiếm những người có đam mê và nhiệt huyết để cùng nhau xây dựng thành công. Đừng bỏ lỡ cơ hội này, ứng tuyển ngay hôm nay và cùng chúng tôi tạo nên những giá trị khác biệt!",
    "Bạn đã sẵn sàng bước vào hành trình phát triển sự nghiệp đầy triển vọng? Chúng tôi đang tìm kiếm những ứng viên nhiệt huyết, sáng tạo để cùng nhau đạt được những thành công mới. Đừng bỏ qua cơ hội này, hãy ứng tuyển ngay hôm nay!",
    "Mỗi ngày đều là một cơ hội để khám phá tiềm năng của bản thân. Hãy gia nhập đội ngũ của chúng tôi và cùng nhau tạo ra những điều tuyệt vời! Ứng tuyển ngay hôm nay để không bỏ lỡ những cơ hội phát triển sự nghiệp thú vị này!",
    "Chúng tôi đang tìm kiếm những người có niềm đam mê và sự sáng tạo không giới hạn. Nếu bạn muốn thử thách bản thân trong một môi trường làm việc đầy thú vị, hãy ứng tuyển ngay hôm nay và cùng chúng tôi đạt được những thành công lớn!",
    "Cơ hội việc làm tuyệt vời không đến thường xuyên! Hãy nhanh chóng ứng tuyển để trở thành một phần của đội ngũ sáng tạo và nhiệt huyết của chúng tôi. Đừng bỏ lỡ cơ hội phát triển bản thân và sự nghiệp, nộp hồ sơ ngay hôm nay!",
    "Bạn có đam mê với công việc? Chúng tôi đang tìm kiếm những ứng viên tài năng và nhiệt huyết để cùng nhau chinh phục những thử thách mới. Hãy gửi hồ sơ ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển sự nghiệp vượt bậc!",
    "Mỗi cơ hội đến đều là một bước tiến trong sự nghiệp của bạn. Chúng tôi đang tìm kiếm những ứng viên đam mê, sáng tạo và sẵn sàng đối mặt với thử thách. Ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội tuyệt vời này!",
    "Hãy đến với chúng tôi và khám phá những cơ hội phát triển sự nghiệp mà bạn luôn mong muốn. Chúng tôi đang tìm kiếm những tài năng sáng tạo, nhiệt huyết và có khát vọng. Đừng bỏ lỡ, ứng tuyển ngay để cùng chúng tôi tạo nên thành công!",
    "Sự nghiệp của bạn chỉ cách một bước đi! Hãy nắm bắt cơ hội này và tham gia đội ngũ của chúng tôi. Chúng tôi chào đón những ứng viên đam mê và sáng tạo để cùng nhau phát triển sự nghiệp trong môi trường năng động và thân thiện!",
    "Bạn đang tìm kiếm một công việc thú vị, đầy thử thách và cơ hội thăng tiến? Hãy tham gia vào đội ngũ của chúng tôi để phát triển bản thân trong môi trường làm việc sáng tạo và đầy năng động. Đừng bỏ qua, ứng tuyển ngay hôm nay!",
    "Chúng tôi đang tìm kiếm những người có đam mê và tài năng để cùng nhau tạo nên những giá trị khác biệt. Môi trường làm việc sáng tạo, đầy thử thách đang chờ đón bạn! Hãy gửi hồ sơ ứng tuyển ngay để bắt đầu hành trình sự nghiệp của bạn!",
    "Bạn đã sẵn sàng cho những thử thách mới? Hãy nắm bắt cơ hội này để phát triển sự nghiệp trong một môi trường chuyên nghiệp, thân thiện và đầy cơ hội. Ứng tuyển ngay hôm nay để không bỏ lỡ những cơ hội phát triển quý giá!",
    "Hãy đến với chúng tôi và khám phá tiềm năng của bản thân! Chúng tôi đang tìm kiếm những ứng viên sáng tạo, nhiệt huyết và muốn thử thách chính mình. Đừng chần chừ, hãy ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển bản thân!",
    "Mỗi ngày là một cơ hội mới để phát triển sự nghiệp. Hãy tham gia cùng chúng tôi để khám phá những thách thức thú vị và cơ hội thăng tiến trong môi trường làm việc năng động. Đừng bỏ lỡ, ứng tuyển ngay hôm nay để không bỏ qua cơ hội tuyệt vời!",
    "Bạn có muốn phát triển sự nghiệp trong một môi trường làm việc đầy thử thách và cơ hội? Hãy ứng tuyển ngay hôm nay và gia nhập đội ngũ tài năng của chúng tôi để cùng nhau tạo nên những giá trị khác biệt và thành công!",
    "Công việc mơ ước của bạn chỉ cách một bước! Hãy nhanh chóng nắm bắt cơ hội này và tham gia vào đội ngũ của chúng tôi để phát triển sự nghiệp trong môi trường năng động và sáng tạo. Đừng bỏ lỡ cơ hội tuyệt vời này, ứng tuyển ngay!",
    "Chúng tôi đang tìm kiếm những ứng viên tài năng và nhiệt huyết để cùng nhau xây dựng một tương lai thành công. Nếu bạn đang tìm kiếm một công việc đầy thử thách và cơ hội, hãy ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển!",
    "Sự nghiệp của bạn sẽ bứt phá khi bạn nắm bắt cơ hội. Chúng tôi đang tìm kiếm những người đam mê, sáng tạo và sẵn sàng đối mặt với thử thách. Đừng bỏ lỡ, hãy ứng tuyển ngay để trở thành một phần của đội ngũ tài năng của chúng tôi!",
    "Một môi trường làm việc thân thiện, sáng tạo và đầy cơ hội thăng tiến đang chờ đón bạn! Hãy ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội phát triển bản thân và sự nghiệp cùng với chúng tôi. Đừng để cơ hội này tuột khỏi tầm tay!",
    "Bạn có sẵn sàng cho những cơ hội mới? Chúng tôi đang tìm kiếm những ứng viên đam mê, sáng tạo và có khát vọng. Hãy gửi hồ sơ ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội làm việc trong môi trường năng động và thân thiện của chúng tôi!",
    "Đừng để cơ hội việc làm tuyệt vời này trôi qua! Hãy nhanh chóng ứng tuyển vào vị trí chúng tôi đang tìm kiếm để phát triển bản thân trong môi trường làm việc sáng tạo, năng động và thân thiện. Ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội!",
    "Chúng tôi đang tìm kiếm những ứng viên tài năng và đam mê để cùng nhau phát triển sự nghiệp. Nếu bạn muốn thử thách bản thân và khám phá những cơ hội mới, hãy ứng tuyển ngay hôm nay để cùng chúng tôi chinh phục những đỉnh cao mới!",
    "Môi trường làm việc sáng tạo, thân thiện và đầy cơ hội phát triển đang chờ đón bạn. Hãy nhanh chóng nắm bắt cơ hội này và ứng tuyển ngay hôm nay để trở thành một phần của đội ngũ thành công và đầy nhiệt huyết của chúng tôi!",
    "Bạn đang tìm kiếm một công việc đầy thử thách và cơ hội phát triển? Chúng tôi đang chờ đón bạn! Hãy nộp hồ sơ ứng tuyển ngay hôm nay để không bỏ lỡ cơ hội làm việc trong môi trường sáng tạo và đầy triển vọng của chúng tôi!",
    "Công việc mơ ước của bạn không còn xa! Hãy nhanh chóng ứng tuyển vào vị trí mà chúng tôi đang tìm kiếm để phát triển bản thân trong môi trường năng động và thân thiện. Đừng bỏ lỡ cơ hội này, hãy ứng tuyển ngay hôm nay!",
    "Thời tiết hôm này thật thoải mái và dễ chịu, tâm trạng mình cũng rất tốt, cuối cùng mình cũng đạt được mục tiêu của mình. Tiếp tục cố gắng cho những điều tốt đẹp phía trước!"
]

# Khởi tạo Socket.IO Client
sio = AsyncClient()

# Dictionary để lưu trữ các instance FacebookBot đang chạy, key là user_id_chat
# Điều này giúp chúng ta truy cập đúng bot khi nhận lệnh từ SocketIO server
running_bots = {}

class FacebookBot:
    def __init__(self, user_id_chat, username, password, two_fa_code):
        self.user_id_chat = user_id_chat
        self.username = username
        self.password = password
        self.two_fa_code = two_fa_code
        self.browser = None
        self.actions = None
        self.id_fb = None # ID của tài khoản Facebook sau khi đăng nhập

        # File cookie riêng cho từng tài khoản
        self.cookie_file = f"fb_cookies_{self.user_id_chat}.json"
        
        # Biến trạng thái online
        self.is_online = False
        self.main_loop_task = None # Để giữ reference đến task chính của bot

    async def _init_browser(self):
        chrome_options = Options()
        prefs = {"profile.managed_default_content_settings.images": 2}
        chrome_options.add_experimental_option("prefs", prefs)
        # chrome_options.add_argument("--headless") # Có thể bật/tắt để debug
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        chrome_options.add_argument(f"user-agent={user_agent}")
        screen_width = 1920
        screen_height = 1050
        chrome_options.add_argument(f"--window-position={screen_width // 2},0")
        chrome_options.add_argument(f"--window-size={screen_width // 2},{screen_height}")
        service = webdriver.ChromeService(version_main=122)
        self.browser = webdriver.Chrome(service=service, options=chrome_options)
        self.browser.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'deviceMemory', {get: () => 8});
            Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 4});
        """)
        self.actions = ActionChains(self.browser)
        
    async def save_cookies(self):
        cookies = self.browser.get_cookies()
        if cookies:
            valid_cookies = [cookie for cookie in cookies if 'expiry' not in cookie or cookie['expiry'] > time.time()]
            with open(self.cookie_file, "w") as file:
                json.dump(valid_cookies, file, indent=4)
            log_message(f"Cookies for {self.username} saved successfully!")
        else:
            log_message(f"No cookies to save for {self.username}.", logging.ERROR)

    async def load_cookies(self):
        if os.path.exists(self.cookie_file) and os.path.getsize(self.cookie_file) > 0:
            try:
                with open(self.cookie_file, "r") as file:
                    cookies = json.load(file)
                valid_cookies = [cookie for cookie in cookies if 'expiry' not in cookie or cookie['expiry'] > time.time()]
                if valid_cookies:
                    for cookie in valid_cookies:
                        # Selenium yêu cầu 'domain' phải khớp với domain hiện tại
                        # Hoặc không có 'domain' để tự động áp dụng.
                        # Nếu cookie có domain không khớp, sẽ lỗi.
                        # Tốt nhất là thêm cookie sau khi đã điều hướng đến facebook.com
                        if 'domain' in cookie and not cookie['domain'].startswith('.'): # Ensure domain starts with . for subdomains
                            cookie['domain'] = '.' + cookie['domain']
                        self.browser.add_cookie(cookie)
                    if len(valid_cookies) < len(cookies):
                        with open(self.cookie_file, "w") as file:
                            json.dump(valid_cookies, file, indent=4)
                        log_message(f"Expired cookies for {self.username} removed and updated JSON file.")
                    log_message(f"Valid cookies for {self.username} loaded successfully!")
                    return True
                else:
                    log_message(f"All cookies for {self.username} have expired. Deleting cookie file...", logging.WARNING)
                    os.remove(self.cookie_file)
            except json.JSONDecodeError:
                log_message(f"Corrupted cookie file for {self.username}. Deleting...", logging.ERROR)
                os.remove(self.cookie_file)
        return False

    async def is_logged_in(self):
        try:
            await asyncio.sleep(3)
            # Kiểm tra sự tồn tại của các phần tử đăng nhập hoặc một phần tử chỉ có khi đăng nhập
            # Ví dụ: icon profile, nút tạo bài viết, v.v.
            # Tìm phần tử ID "email" hoặc "pass" (chỉ xuất hiện khi chưa đăng nhập)
            login_elements = self.browser.find_elements(By.ID, "email") + self.browser.find_elements(By.ID, "pass")
            if login_elements:
                log_message(f"Tài khoản {self.username} chưa đăng nhập vào Facebook (tìm thấy trường đăng nhập)!")
                return False
            
            # Thêm kiểm tra khác: Ví dụ, tìm nút tạo bài viết, hoặc một phần của UI chỉ khi đã đăng nhập
            try:
                # Kiểm tra xem có phần tử News Feed hoặc nút tạo bài viết không
                WebDriverWait(self.browser, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Tạo bài viết công khai'] | //div[@aria-label='Create public post'] | //a[@aria-label='Home'] | //a[@aria-label='Trang chủ']"))
                )
                log_message(f"Tài khoản {self.username} đã đăng nhập vào Facebook (tìm thấy UI đăng nhập)!")
                return True
            except:
                log_message(f"Tài khoản {self.username} chưa đăng nhập vào Facebook (không tìm thấy UI đăng nhập)!")
                return False
        except Exception as e:
            log_message(f"Lỗi khi kiểm tra trạng thái đăng nhập cho {self.username}: {e}", logging.ERROR)
            return False

    async def login(self):
        try:
            txtUser = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, 'email')))
            await type_text_input(txtUser, self.username)
            await asyncio.sleep(random.uniform(1, 3))

            txtPassword = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.ID, 'pass')))
            await type_text_input(txtPassword, self.password)
            await asyncio.sleep(random.uniform(1, 3))

            txtPassword.send_keys(Keys.ENTER)
            await asyncio.sleep(random.uniform(5, 8))
            
            # Sau khi đăng nhập, cố gắng lấy userID
            page_source = self.browser.page_source
            if '"userID":' in page_source:
                start = page_source.find('"userID":') + len('"userID":')
                end = page_source.find(',', start)
                self.id_fb = page_source[start:end]
                log_message(f'ID Facebook của tài khoản {self.username}: {self.id_fb}')
                log_message(f"Đăng nhập tài khoản {self.username} thành công!")
                await self.save_cookies()
                return True
            log_message(f"Không tìm thấy userID sau khi đăng nhập cho {self.username}. Có thể đăng nhập thất bại hoặc cần 2FA.")
            # Xử lý 2FA nếu có
            if self.two_fa_code:
                try:
                    two_fa_input = WebDriverWait(self.browser, 10).until(
                        EC.presence_of_element_located((By.ID, 'approvals_code'))
                    )
                    log_message(f"Yêu cầu mã 2FA cho {self.username}. Nhập mã...")
                    await type_text_input(two_fa_input, self.two_fa_code)
                    two_fa_input.send_keys(Keys.ENTER)
                    await asyncio.sleep(random.uniform(5, 8))
                    if '"userID":' in self.browser.page_source:
                        start = self.browser.page_source.find('"userID":') + len('"userID":')
                        end = self.browser.page_source.find(',', start)
                        self.id_fb = self.browser.page_source[start:end]
                        log_message(f'ID Facebook của tài khoản {self.username}: {self.id_fb}')
                        log_message(f"Đăng nhập 2FA cho {self.username} thành công!")
                        await self.save_cookies()
                        return True
                except Exception as e:
                    log_message(f"Lỗi khi xử lý 2FA cho {self.username}: {e}", logging.ERROR)
            return False
        except Exception as e:
            log_message(f"Đăng nhập tài khoản {self.username} thất bại: {e}",logging.ERROR)
            return False

    async def send_message(self, recipient_url, message_content):
        try:
            log_message(f"Đang gửi tin nhắn '{message_content}' tới {recipient_url} từ tài khoản {self.username}")
            
            # Điều hướng đến trang profile của người nhận
            self.browser.get(recipient_url)
            await asyncio.sleep(random.uniform(4, 6))
            
            send_button = None
            try:
                # Tìm nút "Nhắn tin" hoặc "Message"
                send_button = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[aria-label="Nhắn tin"]'))
                )
            except:
                try:
                    send_button = WebDriverWait(self.browser, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[aria-label="Message"]'))
                    )
                except:
                    log_message("Không tìm thấy nút nhắn tin!", logging.ERROR)
                    # Nếu không tìm thấy nút nhắn tin trên profile, thử truy cập Messenger trực tiếp
                    # Điều này phức tạp hơn vì cần biết Messenger ID của người nhận
                    # Để đơn giản, nếu không có nút nhắn tin trên profile thì coi là lỗi
                    return False
            
            send_button.click()
            await asyncio.sleep(random.uniform(2, 4))

            # Chờ hộp thoại tin nhắn xuất hiện
            message_box_selector = 'div[contenteditable="true"][role="textbox"]'
            post_box = WebDriverWait(self.browser, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, message_box_selector))
            )
            
            # Đôi khi có thể cần click lại vào hộp thoại để kích hoạt
            try:
                post_box.click()
                await asyncio.sleep(1)
            except:
                pass

            p_tag = post_box.find_element(By.TAG_NAME, "p")
            await asyncio.sleep(random.uniform(1, 2))
            
            self.actions.send_keys_to_element(p_tag, message_content)
            await asyncio.sleep(random.uniform(1, 2))
            self.actions.send_keys(Keys.ENTER)
            self.actions.perform()
            await asyncio.sleep(2)
            log_message(f"Tin nhắn đã được gửi thành công từ {self.username} tới {recipient_url}!")
            return True
        except Exception as err:
            log_message(f"Lỗi khi gửi tin nhắn từ {self.username} tới {recipient_url}: {err}", logging.ERROR)
            traceback.print_exc()
            return False

    async def scrape_new_messages(self):
        """
        Cào tin nhắn mới với XPath selectors được cập nhật.
        """
        try:
            log_message(f"Đang cào tin nhắn mới cho tài khoản {self.username}...")
            # Đi tới trang Messenger
            self.browser.get("https://www.facebook.com/messages/")
            await asyncio.sleep(random.uniform(5, 8))

            new_messages = []
            
            # Tìm các cuộc hội thoại có tin nhắn mới
            # Các selector mới cho Facebook 2024
            unread_indicators = self.browser.find_elements(By.XPATH, 
                "//div[contains(@class, 'x1n2onr6') and contains(@class, 'x1ja2u2z')] | " +
                "//div[@role='row' and .//div[contains(@class, 'x1lliihq') and contains(@style, 'font-weight: 700')]] | " +
                "//div[contains(@aria-label, 'unread') or contains(@aria-label, 'chưa đọc')]"
            )
            
            if not unread_indicators:
                log_message(f"Không tìm thấy tin nhắn chưa đọc cho tài khoản {self.username}.")
                return []

            for convo_elem in unread_indicators:
                try:
                    # Lấy thông tin cuộc hội thoại
                    sender_element = convo_elem.find_element(By.XPATH, 
                        ".//span[contains(@class, 'x1lliihq') and contains(@style, 'font-weight: 700')] | " +
                        ".//div[contains(@class, 'x1n2onr6')]//span[contains(@class, 'x1lliihq')]"
                    )
                    
                    sender_name = sender_element.text if sender_element else "Unknown Sender"
                    
                    # Lấy URL của cuộc hội thoại
                    convo_link_element = convo_elem.find_element(By.XPATH, 
                        ".//a[contains(@href, '/t/')] | .//a[contains(@href, '/messages/t/')] | " +
                        ".//div[@role='button' and contains(@data-href, '/t/')]"
                    )
                    conversation_url = convo_link_element.get_attribute('href') or convo_link_element.get_attribute('data-href')

                    if not conversation_url:
                        log_message(f"Không tìm thấy URL hội thoại cho {sender_name}.", logging.WARNING)
                        continue

                    # Click vào hội thoại để xem tin nhắn
                    convo_elem.click()
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    # Cào tin nhắn trong hội thoại
                    message_bubbles = self.browser.find_elements(By.XPATH, 
                        "//div[@role='rowgroup']//div[@role='row'] | " +
                        "//div[contains(@class, 'x1n2onr6') and contains(@class, 'x1ja2u2z')]"
                    )
                    
                    last_message_content = ""
                    last_sender = ""
                    
                    for msg_bubble in reversed(message_bubbles):
                        try:
                            # Xác định tin nhắn của mình hay người khác
                            is_my_message = False
                            try:
                                # Tìm avatar của mình hoặc class đặc biệt
                                msg_bubble.find_element(By.XPATH, 
                                    ".//img[contains(@alt, 'profile picture')] | " +
                                    ".//div[contains(@class, 'x1n2onr6') and contains(@class, 'x1ja2u2z')]"
                                )
                                is_my_message = True
                            except:
                                pass

                            # Lấy nội dung tin nhắn
                            msg_text_elem = msg_bubble.find_element(By.XPATH, 
                                ".//div[contains(@class, 'x1iorvi4')] | " +
                                ".//span[contains(@class, 'x1lliihq')] | " +
                                ".//div[contains(@class, 'x1n2onr6')]//span"
                            )
                            msg_text = msg_text_elem.text.strip() if msg_text_elem else ""
                            
                            if msg_text and not is_my_message:
                                last_message_content = msg_text
                                last_sender = sender_name
                                break
                            elif msg_text and is_my_message:
                                break
                        except Exception as e:
                            continue

                    if last_message_content:
                        # Format tin nhắn theo cấu trúc CRM backend
                        new_messages.append({
                            "participant_name": last_sender,
                            "participant_url": conversation_url,
                            "conversation_url": conversation_url,
                            "content": last_message_content
                        })
                    
                    # Quay lại trang chính
                    self.browser.get("https://www.facebook.com/") 
                    await asyncio.sleep(2)

                except Exception as e:
                    log_message(f"Lỗi khi xử lý cuộc hội thoại cho {self.username}: {e}", logging.ERROR)
                    continue

            if new_messages:
                log_message(f"Tìm thấy {len(new_messages)} tin nhắn mới cho {self.username}. Gửi về CRM.")
                await self._send_new_messages_to_crm(new_messages)
            return new_messages

        except Exception as e:
            log_message(f"Lỗi trong scrape_new_messages cho tài khoản {self.username}: {e}", logging.ERROR)
            traceback.print_exc()
            return []

    async def scrape_notifications(self):
        """
        Cào thông báo mới từ Facebook.
        """
        try:
            log_message(f"Đang cào thông báo mới cho tài khoản {self.username}...")
            
            # Đi tới trang thông báo
            self.browser.get("https://www.facebook.com/notifications/")
            await asyncio.sleep(random.uniform(3, 5))

            notifications = []
            
            # Tìm các thông báo mới
            notification_elements = self.browser.find_elements(By.XPATH, 
                "//div[@role='article' and contains(@class, 'x1n2onr6')] | " +
                "//div[contains(@aria-label, 'notification')] | " +
                "//div[contains(@class, 'x1n2onr6') and contains(@class, 'x1ja2u2z')]"
            )
            
            for notif_elem in notification_elements[:10]:  # Chỉ xử lý 10 thông báo đầu
                try:
                    # Lấy nội dung thông báo
                    content_elem = notif_elem.find_element(By.XPATH, 
                        ".//span[contains(@class, 'x1lliihq')] | " +
                        ".//div[contains(@class, 'x1n2onr6')]//span"
                    )
                    
                    notification_text = content_elem.text if content_elem else ""
                    
                    if notification_text:
                        notifications.append({
                            "type": "notification",
                            "content": notification_text,
                            "timestamp": time.time()
                        })
                        
                except Exception as e:
                    continue

            if notifications:
                log_message(f"Tìm thấy {len(notifications)} thông báo mới cho {self.username}")
                # Có thể gửi thông báo về CRM nếu cần
                await self._send_notifications_to_crm(notifications)
                
            return notifications

        except Exception as e:
            log_message(f"Lỗi trong scrape_notifications cho tài khoản {self.username}: {e}", logging.ERROR)
            return []

    async def _send_notifications_to_crm(self, notifications):
        """Gửi thông báo mới tới CRM Backend"""
        try:
            await sio.emit('new_notifications', {
                'user_id_chat': self.user_id_chat,
                'notifications': notifications
            })
            log_message(f"Đã gửi {len(notifications)} thông báo mới tới CRM Backend")
        except Exception as e:
            log_message(f"Lỗi khi gửi thông báo tới CRM Backend: {e}", logging.ERROR)

    async def run_bot_tasks(self):
        """Các tác vụ định kỳ của bot (lướt FB, xem video, cào tin nhắn và thông báo)"""
        while True:
            try:
                if not self.is_online:
                    log_message(f"Tài khoản {self.username} không online, chờ đợi...")
                    await asyncio.sleep(10)
                    continue

                log_message(f"Bắt đầu các tác vụ định kỳ cho tài khoản {self.username}...")
                
                # Cào tin nhắn mới
                await self.scrape_new_messages()
                await asyncio.sleep(random.uniform(3, 5))
                
                # Cào thông báo mới
                await self.scrape_notifications()
                await asyncio.sleep(random.uniform(3, 5))

                # Sau đó thực hiện các tác vụ lướt FB, tương tác...
                # surf_facebook
                current_url = self.browser.current_url
                if "facebook.com" not in current_url:
                    self.browser.get("https://www.facebook.com")
                    await asyncio.sleep(random.uniform(5, 8))
                
                scroll_count = random.randint(14, 15)
                while scroll_count > 0:            
                    current_scroll = self.browser.execute_script("return window.pageYOffset;")
                    target_scroll = current_scroll + random.randint(600, 1000)
                    await smooth_scroll(self.browser, current_scroll, target_scroll, duration=random.uniform(0.5, 1.5))            
                    await asyncio.sleep(random.uniform(4, 6))

                    if scroll_count % 13 == 0:
                        await self._comment_post()
                        await asyncio.sleep(random.uniform(3, 5))
                    elif scroll_count % 7 == 0:
                        await self._react_post()
                        await asyncio.sleep(random.uniform(3, 5))
                    scroll_count -= 1
                log_message(f"Đã hoàn thành lướt Facebook cho {self.username}")
                
                await asyncio.sleep(random.uniform(2, 5))
                await self._watch_videos()
                await self._post_news_feed()
                await asyncio.sleep(random.uniform(2, 4))
                await self._list_friend()
                await asyncio.sleep(random.uniform(2, 4))
                await self._add_friend()
                
                log_message(f"Hoàn thành một chu kỳ tác vụ cho tài khoản {self.username}. Đang đợi chu kỳ tiếp theo...")
                await asyncio.sleep(random.uniform(200, 300)) # Khoảng thời gian chờ giữa các chu kỳ

            except Exception as e:
                log_message(f"Lỗi trong run_bot_tasks cho tài khoản {self.username}: {e}", logging.ERROR)
                traceback.print_exc()
                # Nếu có lỗi nghiêm trọng, thử đóng và khởi tạo lại trình duyệt
                log_message(f"Đang thử khởi tạo lại trình duyệt cho tài khoản {self.username}...", logging.WARNING)
                self.is_online = False
                await self.quit()
                await asyncio.sleep(10)
                # Cố gắng khởi động lại bot (sẽ cố gắng kết nối lại SocketIO)
                await self.start() 

    # Các hàm tương tác với Facebook khác (react_post, comment_post, share_post, etc.)
    # Cần di chuyển toàn bộ các hàm này vào trong class FacebookBot
    # và thay đổi `browser` thành `self.browser`, `actions` thành `self.actions`.
    # Tôi sẽ chỉ đưa ra một vài ví dụ, bạn hãy làm tương tự với các hàm còn lại.

    async def _react_post(self):
        try:
            like_button = None
            try:
                like_button = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable((By.XPATH, '//div[(@aria-label="Thích" or @aria-label="Like") and @role="button"]'))
                )
            except Exception:
                log_message("Không tìm thấy nút Thích/Like để tương tác.", logging.WARNING)
                return

            self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
            await asyncio.sleep(2)

            selected_reaction = random.choice(REACTIONS)
            log_message(f"Selected reaction: {selected_reaction['name']}")

            actions = self.actions
            actions.move_to_element(like_button).perform()
            await asyncio.sleep(4)

            reaction_button = None
            exact_xpath = selected_reaction['xpath']
            
            try:
                reaction_button = WebDriverWait(self.browser, 5).until(
                    EC.element_to_be_clickable((By.XPATH, exact_xpath))
                )
                log_message(f"Found reaction button with exact xpath for {selected_reaction['name']}")
            except Exception:
                log_message(f"Không tìm thấy reaction button chính xác cho '{selected_reaction['name']}'. Thử XPath chứa từ khóa.", logging.INFO)
                containing_xpath = f'//div[@role="button" and contains(@aria-label, "{selected_reaction["name"]}")]'
                try:
                    reaction_button = WebDriverWait(self.browser, 5).until(
                        EC.element_to_be_clickable((By.XPATH, containing_xpath))
                    )
                    log_message(f"Found reaction button with containing xpath for {selected_reaction['name']}")
                except Exception:
                    log_message(f"Hoàn toàn không tìm thấy reaction button cho '{selected_reaction['name']}'.", logging.WARNING)
                    traceback.print_exc()
                    return

            if not reaction_button:
                log_message(f"Không tìm thấy reaction button với aria-label='{selected_reaction['name']}' sau khi hover.", logging.WARNING)
                return

            self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", reaction_button)
            await asyncio.sleep(1)
            
            actions.move_to_element(reaction_button)
            actions.click()
            actions.perform()
            log_message(f"Đã thả cảm xúc '{selected_reaction['name']}' thành công!")
            await asyncio.sleep(random.uniform(2, 3))

        except Exception as e:
            log_message(f"Lỗi trong hàm _react_post: {e}", logging.ERROR)
            traceback.print_exc()
            pass
    
    async def _comment_post(self):
        try:
            await asyncio.sleep(random.uniform(2, 4))
            comment_buttons = self.browser.find_elements(By.XPATH, '//div[(@aria-label="Viết bình luận" or @aria-label="Leave a comment") and @role="button"]')
            comment_button = None
            for btn in comment_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    comment_button = btn
                    break
            if not comment_button:
                log_message("Không tìm thấy nút bình luận để tương tác.", logging.WARNING)
                return
            self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", comment_button)
            await asyncio.sleep(2)
            self.actions.move_to_element(comment_button)
            self.actions.click()
            self.actions.perform()
            comment_text = random.choice(COMMENTS)
            await asyncio.sleep(random.uniform(2, 4))
            wait = WebDriverWait(self.browser, 10)
            comment_box = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]')))
            await asyncio.sleep(1)
            p_tag = comment_box.find_element(By.TAG_NAME, "p")
            await asyncio.sleep(2)
            self.actions.send_keys_to_element(p_tag, comment_text)
            await asyncio.sleep(random.uniform(2, 4))
            self.actions.send_keys(Keys.ENTER)
            self.actions.perform()  
            await asyncio.sleep(2)
            self.actions.send_keys(Keys.ESCAPE).perform()
            log_message("Đã bình luận bài viết thành công!")
        except Exception as e:
            log_message(f"Error in _comment_post: {e}", logging.ERROR)
            traceback.print_exc()

    async def _share_post(self):
        try:
            share_buttons = self.browser.find_elements(By.XPATH, '//div[(@aria-label="Gửi nội dung này cho bạn bè hoặc đăng lên trang cá nhân của bạn." or @aria-label="Send this to friends or post it on your profile.") and @role="button"]')
            share_button = None
            for btn in share_buttons:
                if btn.is_displayed() and btn.is_enabled():
                    share_button = btn
                    break
            if not share_button:
                log_message("Không tìm thấy nút chia sẻ để tương tác.", logging.WARNING)
                return
            self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", share_button)
            await asyncio.sleep(2)
            self.actions.move_to_element(share_button)
            self.actions.click()
            self.actions.perform()

            await asyncio.sleep(5)
            share_now_button = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//div[(@aria-label="Chia sẻ ngay" or @aria-label="Share now") and @role="button"]'))
            )
            self.actions.move_to_element(share_now_button)
            self.actions.click()
            self.actions.perform()
            log_message("Đã chia sẻ bài viết thành công!")
            await asyncio.sleep(random.uniform(2, 3))
        except Exception as e:
            log_message(f"Error in _share_post: {e}", logging.ERROR)
            traceback.print_exc()

    async def _watch_videos(self):
        try:
            self.browser.get("https://www.facebook.com/watch/")
            await asyncio.sleep(random.uniform(3, 6))
            scroll_count_video = random.randint(6, 15)
            while scroll_count_video > 0:
                log_message(f"scroll_count_watch_video {scroll_count_video}")

                await asyncio.sleep(random.uniform(4, 7))

                video_selected = self.browser.find_elements(By.XPATH, "//div[contains(@class, 'x1ey2m1c') and contains(@class, 'x9f619')]")

                visible_videos = [video for video in video_selected if video.is_displayed()]
                await asyncio.sleep(random.uniform(40, 60))

                if visible_videos:
                    log_message(f"Found {len(visible_videos)} visible videos.")
                    current_video = visible_videos[0]

                    if scroll_count_video % 7 == 0 or scroll_count_video % 13 == 0:
                        if scroll_count_video % 7 == 0:
                            await asyncio.sleep(random.uniform(5, 7))
                            like_buttons = self.browser.find_elements(By.XPATH, "//span[@data-ad-rendering-role='like_button']")
                            like_button = None
                            for btn in like_buttons:
                                if btn.is_displayed() and btn.is_enabled():
                                    like_button = btn
                                    break
                            if like_button:
                                self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", like_button)
                                await asyncio.sleep(random.uniform(1, 3))
                                like_button.click()
                                log_message("Liked the post video successfully!")
                            else:
                                log_message("Like button is not visible, skipping...")

                        elif scroll_count_video % 13 == 0:
                            await self._share_post()
                            await asyncio.sleep(random.uniform(3, 5))
                            
                        await asyncio.sleep(random.uniform(2, 5))

                        self.actions.move_to_element(current_video).click().perform()
                        await asyncio.sleep(random.uniform(3, 5))
                        
                        video_url = self.browser.current_url
                        log_message(f"current_url: {video_url}")
                else:
                    log_message("No visible videos found, continuing...")

                scroll_count_video -= 1

                current_scroll = self.browser.execute_script("return window.pageYOffset;")
                target_scroll = current_scroll + random.randint(600, 800)
                await smooth_scroll(self.browser, current_scroll, target_scroll, duration=random.uniform(0.5, 1.5))
                    
            log_message("Đã hoàn thành xem video Facebook")
            
        except Exception as err:
            log_message(f"err watch videos {err}", logging.ERROR)
            traceback.print_exc()
    
    async def _post_news_feed(self, content=None, post_id=None):
        """
        Đăng bài lên Facebook.
        Nếu content được cung cấp, sử dụng content đó thay vì random.
        Nếu post_id được cung cấp, gửi trạng thái về CRM.
        """
        try:
            await asyncio.sleep(random.uniform(5, 8))
            actions = self.actions
            home = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@aria-label='Home' or @aria-label='Trang chủ']"))
            )
            home.click()
            await asyncio.sleep(random.uniform(5, 8))
            h3_post = self.browser.find_element(By.XPATH, "//div[@class='xi81zsa x1lkfr7t xkjl1po x1mzt3pk xh8yej3 x13faqbe']")
            h3_post.click()
            post_box = WebDriverWait(self.browser, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[contenteditable="true"]')))
            await asyncio.sleep(1)

            p_tag = post_box.find_element(By.TAG_NAME, "p")

            if(p_tag and p_tag.is_displayed()):
                await asyncio.sleep(2)
                # Sử dụng content được cung cấp hoặc random
                post_content = content if content else random.choice(CONTENT_POST)
                actions.send_keys_to_element(p_tag, post_content)
                await asyncio.sleep(random.uniform(2, 4))
                actions.perform()
                await asyncio.sleep(2)
                try:
                    post_new_button = self.browser.find_element(By.CSS_SELECTOR, "div[aria-label='Đăng']")
                except:
                    post_new_button = self.browser.find_element(By.CSS_SELECTOR, "div[aria-label='Post']")
                await asyncio.sleep(2)
                post_new_button.click()
                log_message("Đã đăng bài viết thành công!")
                
                # Gửi trạng thái thành công về CRM nếu có post_id
                if post_id:
                    await self._send_post_status_to_crm(post_id, "success")
            await asyncio.sleep(random.uniform(2, 4))
        except Exception as err:
            log_message(f"err post new feed {err}", logging.ERROR)
            traceback.print_exc()
            # Gửi trạng thái thất bại về CRM nếu có post_id
            if post_id:
                await self._send_post_status_to_crm(post_id, "failed", str(err))
            pass
    
    async def _list_friend(self):
        try:
            list_friend = []
            self.browser.get("https://www.facebook.com/friends/list")
            await asyncio.sleep(random.uniform(2, 4))
            friends_box = self.browser.find_element(By.XPATH, "//div[@class='x135pmgq']")
            log_message(f"friends_box: {friends_box}")
            await asyncio.sleep(random.uniform(1, 3))
            friends_link = friends_box.find_elements(By.XPATH, ".//a[contains(@class, 'x1qjc9v5') and contains(@class, 'xjbqb8w') and contains(@class, 'xde0f50') and contains(@class, 'x1lliihq')]")

            for link in friends_link:
                link_friend = link.get_attribute('href')
                if link_friend:
                    list_friend.append(link_friend)
            
            await asyncio.sleep(random.uniform(4, 6))
            log_message(f"list_friend: {list_friend}")
            if not list_friend:
                log_message("Không tìm thấy bạn bè nào trong danh sách!", logging.WARNING)
                return
            await self.send_message(random.choice(list_friend), random.choice(CONTENT_POST))
            
        except Exception as err:
            log_message(f"err list_friend {err}", logging.ERROR)
            traceback.print_exc()
            pass
    
    async def _add_friend(self):
        try:
            log_message("Bắt đầu quy trình thêm bạn bè.", logging.INFO)

            log_message("Tìm kiếm các nhóm tuyển dụng...", logging.INFO)
            self.browser.get("https://www.facebook.com/search/groups?q=tuyển%20dụng")
            await asyncio.sleep(random.uniform(3, 5))
            groups_box = self.browser.find_elements(By.XPATH, '//a[contains(@href, "/groups/") and @aria-hidden="true"]')
            group_links = [g.get_attribute("href") for g in groups_box if g.is_displayed() and g.get_attribute("href")]

            link_group = random.choice(group_links)

            members_url = link_group.rstrip("/") + "/members"
            self.browser.get(members_url)
            await asyncio.sleep(random.uniform(5, 8))

            for i in range(5):
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                await asyncio.sleep(random.uniform(2, 4))

            add_friend_buttons = self.browser.find_elements(
                By.XPATH,
                "//div[@role='button' and (starts-with(@aria-label, 'Kết bạn với ') or starts-with(@aria-label, 'Add Friend'))]"
            )

            profile_info_to_add = []
            for idx, btn in enumerate(add_friend_buttons):
                try:
                    aria_label = btn.get_attribute('aria-label')
                    user_name = ''
                    if aria_label:
                        if aria_label.startswith('Kết bạn với '):
                            user_name = aria_label[len('Kết bạn với '):].strip()
                        elif aria_label.startswith('Add Friend'):
                            user_name = aria_label[len('Add Friend'):].strip()
                    
                    profile_link_element = None
                    member_card_xpath = "./ancestor::div[contains(@class, 'x1ja2u2z')][1]"
                    member_card = None
                    member_card = btn.find_element(By.XPATH, member_card_xpath)
                    if member_card:
                        xpath_profile_link = f".//a[@role='link' and (contains(., '{user_name}') or @aria-label='{user_name}') and (contains(@href, '/user/') or contains(@href, 'profile.php?id='))]"
                        try:
                            profile_link_element = member_card.find_element(By.XPATH, xpath_profile_link)
                        except Exception:
                            xpath_profile_link = ".//a[@role='link' and (contains(@href, '/user/') or contains(@href, 'profile.php?id='))]"
                            try:
                                profile_link_element = member_card.find_element(By.XPATH, xpath_profile_link)
                            except Exception:
                                pass
                    if profile_link_element:
                        link_user = profile_link_element.get_attribute('href')
                        if link_user and not link_user.startswith("http"):
                            link_user = "https://www.facebook.com" + link_user
                        
                        if link_user:
                            profile_info_to_add.append((link_user, user_name, btn))
                        else:
                            log_message(f"Liên kết profile rỗng sau khi tìm thấy phần tử cho '{user_name}'.", logging.WARNING)
                    else:
                        log_message(f"Không tìm thấy phần tử liên kết profile nào cho '{user_name}'.", logging.WARNING)
                except Exception as e:
                    log_message(f"Lỗi khi xử lý nút Kết bạn (chung): {e}", logging.ERROR)
                    traceback.print_exc()
                    continue

            if not profile_info_to_add:
                log_message("Không tìm thấy nút 'Kết bạn' nào khả dụng.", logging.WARNING)
                return

            link_user, user_name, add_btn = random.choice(profile_info_to_add)
            
            self.browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
            await asyncio.sleep(random.uniform(1, 2))
            
            try:
                add_btn.click()
                log_message(f"Đã gửi lời mời kết bạn thành công tới {user_name}!", logging.INFO)
            except Exception as click_err:
                log_message(f"Không thể click nút 'Kết bạn': {click_err}. Thử click bằng JavaScript.", logging.WARNING)
                self.browser.execute_script("arguments[0].click();", add_btn)
                log_message(f"Đã gửi lời mời kết bạn thành công tới {user_name} (qua JS click)!", logging.INFO)

            await asyncio.sleep(random.uniform(2, 4))
            await self.send_message(link_user, "Chào bạn, mình là nhân sự bên timviec365, bạn cho mình hỏi là bạn đang đi tìm việc hay là bên tuyển dụng đó ạ? Nếu bạn đang cần tìm ứng viên hoặc đang cần tìm việc làm thì bạn lên trang web timviec365.vn tham khảo nhé.")

        except Exception as err:
            log_message(f"Lỗi tổng quát trong hàm _add_friend: {err}", logging.ERROR)
            traceback.print_exc()
            pass


    async def start(self):
        initialize()
        await self._init_browser()
        
        # Điều hướng đến Facebook trước khi load cookie để domain cookie khớp
        self.browser.get("https://facebook.com")
        await asyncio.sleep(3)
        
        logged_in = False
        if await self.load_cookies():
            self.browser.refresh() # Refresh lại trang sau khi add cookie
            await asyncio.sleep(4)
            logged_in = await self.is_logged_in()
        
        if not logged_in:
            log_message(f"Cookies cho tài khoản {self.username} không hợp lệ hoặc hết hạn, cần đăng nhập lại.")
            if await self.login():
                logged_in = await self.is_logged_in()
            if not logged_in:
                log_message(f"Đăng nhập tài khoản {self.username} thất bại sau khi thử. Bot sẽ dừng lại.", logging.ERROR)
                self.is_online = False
                # Gửi trạng thái offline về CRM
                await sio.emit('status_update', {'user_id_chat': self.user_id_chat, 'status': 'offline'})
                return
            
        # Cố gắng lấy Facebook ID sau khi đăng nhập thành công
        if '"userID":' in self.browser.page_source:
            start_index = self.browser.page_source.find('"userID":') + len('"userID":')
            end_index = self.browser.page_source.find(',', start_index)
            self.id_fb = self.browser.page_source[start_index:end_index].strip()
            log_message(f'ID Facebook của tài khoản {self.username}: {self.id_fb}')
            self.is_online = True
            # Gửi trạng thái online về CRM qua SocketIO
            await sio.emit('status_update', {'user_id_chat': self.user_id_chat, 'status': 'online', 'id_fb': self.id_fb})
            log_message(f"Tài khoản {self.username} đã online.")
        else:
            self.is_online = False
            await sio.emit('status_update', {'user_id_chat': self.user_id_chat, 'status': 'offline'})
            log_message(f"Không thể lấy ID Facebook cho tài khoản {self.username}. Có thể chưa đăng nhập hoặc lỗi.", logging.ERROR)
        
        # Đăng ký bot với CRM Backend
        if self.is_online:
            await self._register_with_crm()
            # Chạy các tác vụ bot trong một asyncio task riêng
            self.main_loop_task = asyncio.create_task(self.run_bot_tasks())

    async def _register_with_crm(self):
        """Đăng ký bot với CRM Backend"""
        try:
            await sio.emit('bot_register', {
                'user_id_chat': self.user_id_chat
            })
            log_message(f"Bot {self.user_id_chat} đã đăng ký với CRM Backend")
        except Exception as e:
            log_message(f"Lỗi khi đăng ký với CRM Backend: {e}", logging.ERROR)

    async def _send_new_messages_to_crm(self, messages):
        """Gửi tin nhắn mới tới CRM Backend"""
        try:
            await sio.emit('new_messages', {
                'user_id_chat': self.user_id_chat,
                'messages': messages
            })
            log_message(f"Đã gửi {len(messages)} tin nhắn mới tới CRM Backend")
        except Exception as e:
            log_message(f"Lỗi khi gửi tin nhắn tới CRM Backend: {e}", logging.ERROR)

    async def _send_post_status_to_crm(self, post_id, status, error_message=""):
        """Gửi trạng thái đăng bài tới CRM Backend"""
        try:
            await sio.emit('post_status_update', {
                'post_id': post_id,
                'status': status,
                'error_message': error_message
            })
            log_message(f"Đã gửi trạng thái đăng bài {status} tới CRM Backend")
        except Exception as e:
            log_message(f"Lỗi khi gửi trạng thái đăng bài tới CRM Backend: {e}", logging.ERROR)

    async def quit(self):
        if self.browser:
            try:
                if self.main_loop_task:
                    self.main_loop_task.cancel() # Hủy task chính của bot
                    log_message(f"Task chính của bot {self.username} đã bị hủy.")
                self.browser.quit()
                log_message(f"Đã đóng browser cho tài khoản {self.username}.", logging.INFO)
            except Exception as e:
                log_message(f"Lỗi khi đóng browser cho {self.username}: {e}", logging.WARNING)
            finally:
                self.is_online = False
                # Gửi trạng thái offline về CRM
                await sio.emit('status_update', {'user_id_chat': self.user_id_chat, 'status': 'offline'})


# --- Socket.IO Client Event Handlers ---
@sio.event
async def connect():
    user_id_chat = os.getenv('USER_ID_CHAT') # Lấy USER_ID_CHAT từ biến môi trường
    if user_id_chat:
        # Gửi header khi connect để server có thể định danh bot
        # headers={'X-User-ID-Chat': user_id_chat} được thêm vào lúc sio.connect
        log_message(f"Socket.IO client cho bot {user_id_chat} đã kết nối tới CRM Backend.")
    else:
        log_message("Socket.IO client kết nối nhưng không có USER_ID_CHAT.")

@sio.event
async def disconnect():
    user_id_chat = os.getenv('USER_ID_CHAT')
    log_message(f"Socket.IO client cho bot {user_id_chat} đã ngắt kết nối.")
    if user_id_chat in running_bots:
        # Cập nhật trạng thái bot là offline
        running_bots[user_id_chat].is_online = False

@sio.event
async def connect_error(data):
    user_id_chat = os.getenv('USER_ID_CHAT')
    log_message(f"Socket.IO client cho bot {user_id_chat} kết nối lỗi: {data}", logging.ERROR)
    if user_id_chat in running_bots:
        running_bots[user_id_chat].is_online = False


@sio.on('send_message_command')
async def on_send_message_command(data):
    """
    Lắng nghe lệnh gửi tin nhắn từ CRM Backend.
    """
    user_id_chat = data.get('user_id_chat')
    recipient_url = data.get('recipient_url')
    message_content = data.get('message_content')
    
    log_message(f"Nhận lệnh gửi tin nhắn cho bot {user_id_chat}: '{message_content}' tới '{recipient_url}'")

    if user_id_chat in running_bots:
        bot = running_bots[user_id_chat]
        if bot.is_online:
            await bot.send_message(recipient_url, message_content)
        else:
            log_message(f"Bot {user_id_chat} không online, không thể gửi tin nhắn.", logging.WARNING)
    else:
        log_message(f"Nhận lệnh gửi tin nhắn cho bot {user_id_chat} nhưng bot không chạy.", logging.WARNING)

@sio.on('post_news_feed_command')
async def on_post_news_feed_command(data):
    """
    Lắng nghe lệnh đăng bài từ CRM Backend.
    """
    user_id_chat = data.get('user_id_chat')
    content = data.get('content')
    post_id = data.get('post_id')
    
    log_message(f"Nhận lệnh đăng bài cho bot {user_id_chat}: post_id={post_id}")

    if user_id_chat in running_bots:
        bot = running_bots[user_id_chat]
        if bot.is_online:
            await bot._post_news_feed(content, post_id)
        else:
            log_message(f"Bot {user_id_chat} không online, không thể đăng bài.", logging.WARNING)
            # Gửi trạng thái thất bại về CRM
            await bot._send_post_status_to_crm(post_id, "failed", "Bot không online")
    else:
        log_message(f"Nhận lệnh đăng bài cho bot {user_id_chat} nhưng bot không chạy.", logging.WARNING)


async def run_facebook_bot_and_socketio(account_data):
    """
    Hàm chính để chạy bot Facebook và quản lý kết nối Socket.IO của nó.
    """
    user_id_chat = str(account_data.get("user_id_chat"))
    
    # Thiết lập biến môi trường để SocketIO client có thể đọc
    os.environ['USER_ID_CHAT'] = user_id_chat

    bot = FacebookBot(
        user_id_chat=user_id_chat,
        username=account_data.get("facebook_username"),
        password=account_data.get("facebook_password"),
        two_fa_code=account_data.get("facebook_2fa_code", "")
    )
    running_bots[user_id_chat] = bot

    # Kết nối Socket.IO client tới CRM Backend
    try:
        # Thay thế 'http://localhost:5000' bằng địa chỉ IP/domain thực tế của CRM Backend
        # Nếu CRM Backend chạy trên một máy chủ khác
        await sio.connect('http://localhost:5000', transports=['websocket'],
                          headers={'X-User-ID-Chat': user_id_chat})
    except Exception as e:
        log_message(f"Lỗi khi kết nối Socket.IO tới CRM Backend cho bot {user_id_chat}: {e}", logging.ERROR)
        # Nếu không kết nối được SocketIO, bot không thể báo cáo trạng thái/nhận lệnh
        # Bạn có thể quyết định dừng bot hoặc để nó tiếp tục chạy các tác vụ định kỳ
        # và thử kết nối lại SocketIO sau. Ở đây, ta sẽ cố gắng tiếp tục.

    await bot.start() # Bắt đầu các tác vụ của bot

    # Đảm bảo client SocketIO duy trì kết nối
    await sio.wait() # Giữ chương trình chạy miễn là SocketIO kết nối

if __name__ == "__main__":
    if len(sys.argv) > 1:
        client_user_id_chat = sys.argv[1]
        try:
            with open("user_accounts.json", "r", encoding="utf-8") as file:
                accounts = json.load(file)
                account_data_found = None
                for acc in accounts:
                    if str(acc.get("user_id_chat")) == client_user_id_chat:
                        account_data_found = acc
                        break
                if not account_data_found:
                    log_message(f"Tài khoản với user_id_chat '{client_user_id_chat}' không được tìm thấy trong user_accounts.json. Chương trình sẽ dừng lại.", logging.ERROR)
                    sys.exit(1)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            log_message(f"Lỗi khi đọc file user_accounts.json: {e}", logging.ERROR)
            sys.exit(1)

        log_message(f"Khởi động bot cho user_id_chat: {client_user_id_chat}")
        asyncio.run(run_facebook_bot_and_socketio(account_data_found))
    else:
        print("Usage: python toolfacebook.py <user_id_chat>")
        sys.exit(1)