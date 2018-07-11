$(function () {
  let lastPage = 1
  let currentPage = 0

  // DOM 로딩 완료 시 데이터 전체 수 조회
  $.ajax({
    url: '/info/datacount',
    dataType: 'json',
    method: 'GET',
    async: false,
    success (result) {
      lastPage = result.count
      console.log(lastPage)
    },
    error (e) {
      console.log(e)
    }
  })

  // 데이터 수 조회 버튼
  $('#data-count').click(function () {
    $.ajax({
      url: '/info/datacount',
      dataType: 'json',
      method: 'GET',
      success (result) {
        console.log(result)
        $('#result').html('')
        $('#image').attr('src', '')
        $('#result-area').text(JSON.stringify(result))
      },
      error (e) {
        console.log(e)
      }
    })
  })

  // 크롤러 설정 정보 조회 버튼
  $('#config-info').click(function () {
    $.ajax({
      url: '/info/setting',
      dataType: 'json',
      method: 'GET',
      success (result) {
        console.log(result)
        $('#result').html('')
        $('#image').attr('src', '')
        $('#result-area').text(JSON.stringify(result))
      },
      error (e) {
        console.log(e)
      }
    })
  })

  // 저작물 범위 조회 버튼
  $('#get-all').click(function () {
    // 시작 인덱스
    const start = $('#start-val').val()
    // 갯수
    const count = $('#count-val').val()
    $.ajax({
      url: `/info/datarange?start=${start}&count=${count}`,
      dataType: 'json',
      method: 'GET',
      success (result) {
        let count = 0
        console.log(result.list)
        $('#result').html('')
        $('#result-area').html('')
        $('#image').attr('src', '')
        for (let image of result.list) {
          $('#result-area').append(`<img style="width: 100px; height: 100px;"src="data:image/png;base64,${image.hash}"><br>`)
          $('#result-area').append(`저작물 ID: ${image.id}<br>해시값은 임시로 대체 됨<br>${JSON.stringify(image.info)}<br><br><br>`)
        }
      },
      error (e) {
        console.log(e)
      }
    })
  })

  // 저작물 조회 버튼
  $('#get-id').click(function () {
    const value = $('#id-val').val()
    if (value === '') {
      $('#result').text('아이디를 입력해주세요')
      return
    }
    
    $.ajax({
      url: '/info/original',
      data: {id: value},
      dataType: 'json',
      method: 'GET',
      async: false,
      success (result) {
        console.log(result)
        $('#result-area').text(JSON.stringify(result))
        
        /* 기존 영역 지우기 */
        $('#result').html('')
        try {
          Object.keys(result).forEach(k => {
            if (result[k]) {
              let row = 
              `<tr>
                <td>${k.toUpperCase()}</td>
                <td>${result[k]}</td>
              </tr>`
              /* 표 영역에 추가 */
              $('#result').append(row)
            }
          })
        } catch (e) {
          console.log('저작물이 없습니다.')
        }
      },
      error (e) {
        console.log(e)
      }
    })
    
    $.ajax({
      url: '/info/hash/original',
      data: {id: value},
      dataType: 'json',
      method: 'GET',
      async: false,
      success (result) {
        console.log(result)
        /* 응답 객체에 해시데이터가 있을 경우 이미지 출력 */
        if (result.hashimg) {
          $('#image').attr('src', 'data:image/png;base64,' + result.hashimg)
        } else {
          $('#image').attr('src', '')
        }
      },
      error (e) {
        console.log(e)
      }
    })

    $.ajax({
      url: '/info/hash/thumbnail',
      data: {id: value},
      dataType: 'json',
      method: 'GET',
      async: false,
      success (result) {
        console.log(result)
        /* 응답 객체에 해시데이터가 있을 경우 이미지 출력 */
        if (result.hashthumbnail) {
          $('#image-thumb').attr('src', 'data:image/png;base64,' + result.hashhumbnail)
        } else {
          $('#image-thumb').attr('src', '')
        }
      },
      error (e) {
        console.log(e)
      }
    })
  })

  // 라이선스 정보 버튼
  $('#get-license').click(function () {
    const value = $('#id-val').val()
    if (value === '') {
      $('#result-area').text('아이디를 입력해주세요')
      return
    }
    $.ajax({
      url: ('/info/license'),
      data: {id: value},
      dataType: 'json',
      method: 'GET',
      success (result) {
        console.log(result)
        $('#result-license').text(JSON.stringify(result))
      },
      error (e) {
        console.log(e)
      }
    })
    $.ajax({
      url: ('/info/hash/license'),
      data: {id: value},
      dataType: 'json',
      method: 'GET',
      success (result) {
        if (result.hashlicense) {
          $('#image-license').attr('src', 'data:image/png;base64,' + result.hashlicense)
        } else {
          $('#image-license').attr('src', '')
        }
      },
      error (e) {
        console.log(e)
      }
    })
  })

  // 게시물 삭제 버튼
  $('#del-id').click(function () {
    const value = $('#id-val').val()
    if (value === '') {
      $('#result-area').text('아이디를 입력해주세요')
      return
    }
    $.ajax({
      url: ('/data/' + value),
      dataType: 'json',
      method: 'DELETE',
      success (result) {
        console.log(result)
        $('#result').text(JSON.stringify(result))
      },
      error (e) {
        console.log(e)
      }
    })
  })

  // 페이징 버튼 (다음)
  $('#next').click(function () {
    if (currentPage >= parseInt((lastPage + 9) / 9)) {
      alert('다음 페이지가 없습니다.')
      return
    }
    currentPage += 1
    const start = (currentPage - 1) * 9
    $.ajax({
      url: ('/info/datarange'),
      data: {start: start, count: 9},
      dataType: 'json',
      method: 'GET',
      success (result) {
        console.log(result.list)
        $('#page-image-list').html('')
        for (let image of result.list) {
          html = `
          <div class="list-image-area">
            <img class="list-image" src="data:image/png;base64,${image.hash}">
          </div>
          `
          $('#page-image-list').append(html)
        }
        $('#page-image-list').append(`<br><br><b>${currentPage} 페이지</b>`)
      },
      error (e) {
        console.log(e)
      }
    })
  })

  // 페이징 버튼 (이전)
  $('#prev').click(function () {
    if (currentPage <= 1) {
      alert('이전 페이지가 없습니다.')
      return
    }
    currentPage -= 1
    const start = (currentPage - 1) * 9
    $.ajax({
      url: ('/info/datarange'),
      data: {start: start, count: 9},
      dataType: 'json',
      method: 'GET',
      success (result) {
        console.log(result.list)
        $('#page-image-list').html('')
        for (let image of result.list) {
          html = `
          <div class="list-image-area">
            <img class="list-image" src="data:image/png;base64,${image.hash}">
          </div>
          `
          $('#page-image-list').append(html)
        }
        $('#page-image-list').append(`<br><br><b>${currentPage} 페이지</b>`)
      },
      error (e) {
        console.log(e)
      }
    })
  })

  // 페이징 버튼 처음
  $('#first').click(function () {
    currentPage = 1
    const start = 0
    $.ajax({
      url: ('/info/datarange'),
      data: {start: start, count: 9},
      dataType: 'json',
      method: 'GET',
      success (result) {
        console.log(result.list)
        $('#page-image-list').html('')
        for (let image of result.list) {
          html = `
          <div class="list-image-area">
            <img class="list-image" src="data:image/png;base64,${image.hash}">
          </div>
          `
          $('#page-image-list').append(html)
        }
        $('#page-image-list').append(`<br><br><b>${currentPage} 페이지</b>`)
      },
      error (e) {
        console.log(e)
      }
    })
  })

  // 페이징 버튼 (끝)
  $('#last').click(function () {
    currentPage = parseInt((lastPage + 9) / 9)
    const start = (currentPage-1) * 9
    $.ajax({
      url: ('/info/datarange'),
      data: {start: start, count: 9},
      dataType: 'json',
      method: 'GET',
      success (result) {
        console.log(result.list)
        $('#page-image-list').html('')
        for (let image of result.list) {
          html = `
          <div class="list-image-area">
            <img class="list-image" src="data:image/png;base64,${image.hash}">
          </div>
          `
          $('#page-image-list').append(html)
        }
        $('#page-image-list').append(`<br><br><b>${currentPage} 페이지</b>`)
      },
      error (e) {
        console.log(e)
      }
    })
  })

  // 지정 페이지로 이동
  $('#goto').click(function () {
    const page = parseInt($('#goto-page').val())
    $('#goto-page').val("")
    currentPage = page
    $.ajax({
      url: ('/info/datarange'),
      data: {start: (currentPage - 1) * 9, count: 9},
      dataType: 'json',
      method: 'GET',
      success (result) {
        console.log(result.list)
        $('#page-image-list').html('')
        for (let image of result.list) {
          html = `
          <div class="list-image-area">
            <img class="list-image" src="data:image/png;base64,${image.hash}">
          </div>
          `
          $('#page-image-list').append(html)
        }
        $('#page-image-list').append(`<br><br><b>${currentPage} 페이지</b>`)
      },
      error (e) {
        console.log(e)
      }
    })
  })
})
