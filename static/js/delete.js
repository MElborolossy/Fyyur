onClickDelete = () => {
    let venue_id = document.getElementById('delBtn').getAttribute('data')
    fetch(`/venues/${venue_id}`, {
        method: 'DELETE',
    }).then( () => {
        document.location.href = "/"
    });
};